import time
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import TransferCancelled
from src.interfaces.api import session_app

client = TestClient(session_app.app)


def _wait_for_job(job_id: str, timeout: float = 3.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/transfer/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        if data["status"] in {"done", "cancelled", "error"}:
            return data
        time.sleep(0.02)
    pytest.fail(f"job {job_id} did not finish before timeout")


def test_home_injects_session_script() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert '/static/session.js?v=1' in response.text


def test_create_job_runs_csv_transfer_and_replays_events(tmp_path) -> None:
    source = tmp_path / "source.csv"
    target = tmp_path / "target.csv"
    pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]}).to_csv(source, index=False)

    response = client.post(
        "/transfer/jobs",
        data={
            "source_type": "csv",
            "target_type": "csv",
            "source": str(source),
            "target": str(target),
            "source_sep_file": ",",
            "target_sep_file": ",",
            "chunk_size": "1",
        },
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    status = _wait_for_job(job_id)
    assert status["status"] == "done"
    assert status["rows_read"] == 3
    assert status["rows_written"] == 3
    assert status["can_cancel"] is False

    exported = pd.read_csv(target)
    assert exported["id"].tolist() == [1, 2, 3]

    stream = client.get(f"/transfer/jobs/{job_id}/stream?after=0")
    assert stream.status_code == 200
    assert '"type": "start"' in stream.text
    assert '"type": "progress"' in stream.text
    assert '"type": "done"' in stream.text

    completed_cancel = client.post(f"/transfer/jobs/{job_id}/cancel")
    assert completed_cancel.status_code == 200
    assert completed_cancel.json()["accepted"] is False


def test_cancel_running_job(monkeypatch) -> None:
    class SlowReader:
        def read_chunks(self, *args, **kwargs):
            for value in range(200):
                time.sleep(0.005)
                yield pd.DataFrame({"id": [value]})

    class FakeWriter:
        def __init__(self) -> None:
            self.closed = False

        def write(self, data, *args, **kwargs):
            return len(data)

        def close(self) -> None:
            self.closed = True

    writer = FakeWriter()
    monkeypatch.setattr(session_app, "build_reader", lambda **kwargs: SlowReader())
    monkeypatch.setattr(session_app, "build_writer", lambda **kwargs: writer)

    response = client.post(
        "/transfer/jobs",
        data={
            "source_type": "csv",
            "target_type": "csv",
            "source": "slow-source.csv",
            "target": "partial-target.csv",
            "chunk_size": "1",
        },
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    cancel = client.post(f"/transfer/jobs/{job_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["accepted"] is True

    status = _wait_for_job(job_id)
    assert status["status"] == "cancelled"
    assert writer.closed is True

    stream = client.get(f"/transfer/jobs/{job_id}/stream")
    assert '"type": "cancel_requested"' in stream.text
    assert '"type": "cancelled"' in stream.text


def test_job_failure_is_exposed_as_error(monkeypatch) -> None:
    def fail_reader(**kwargs):
        raise RuntimeError("reader exploded")

    monkeypatch.setattr(session_app, "build_reader", fail_reader)

    response = client.post(
        "/transfer/jobs",
        data={
            "source_type": "csv",
            "target_type": "csv",
            "source": "source.csv",
            "target": "target.csv",
            "chunk_size": "1",
        },
    )
    job_id = response.json()["job_id"]

    status = _wait_for_job(job_id)
    assert status["status"] == "error"
    assert status["error"] == "reader exploded"

    stream = client.get(f"/transfer/jobs/{job_id}/stream")
    assert '"type": "error"' in stream.text
    assert "reader exploded" in stream.text


def test_job_endpoints_return_404_for_unknown_job() -> None:
    missing = "does-not-exist"

    assert client.get(f"/transfer/jobs/{missing}").status_code == 404
    assert client.post(f"/transfer/jobs/{missing}/cancel").status_code == 404
    assert client.get(f"/transfer/jobs/{missing}/stream").status_code == 404


def test_create_job_validates_form() -> None:
    response = client.post(
        "/transfer/jobs",
        data={
            "source_type": "sqlite",
            "target_type": "csv",
            "source": "source.db",
            "target": "target.csv",
            "chunk_size": "1",
        },
    )

    assert response.status_code == 400
    assert "tabela" in response.json()["error"].lower()


def test_normalise_sqlserver_oracle_and_bigquery_fields() -> None:
    sql_to_oracle = session_app._normalise_form(
        {
            "source_type": "sqlserver",
            "target_type": "oracle",
            "source_connection_string": "DRIVER=X;SERVER=db;",
            "source_table_name_sql": "dbo.source_table",
            "target_oracle_dsn": "user/pass@db/service",
            "target_table_name_oracle": "APP.TARGET_TABLE",
            "chunk_size": "500",
        }
    )
    assert sql_to_oracle["source"] == "DRIVER=X;SERVER=db;"
    assert sql_to_oracle["source_table_name"] == "dbo.source_table"
    assert sql_to_oracle["target"] == "user/pass@db/service"
    assert sql_to_oracle["target_table_name"] == "APP.TARGET_TABLE"
    assert sql_to_oracle["chunk_size"] == 500

    bq = session_app._normalise_form(
        {
            "source_type": "bigquery",
            "target_type": "bigquery",
            "source_bq_credentials_file": "/tmp/source.json",
            "target_bq_credentials_file": "/tmp/target.json",
            "source_table_name_bq": "dataset.source",
            "target_table_name_bq": "dataset.target",
            "source_bq_project_id": "project-a",
            "target_bq_project_id": "project-b",
            "chunk_size": "0",
        }
    )
    assert bq["source"] == "/tmp/source.json"
    assert bq["target"] == "/tmp/target.json"
    assert bq["source_table_name"] == "dataset.source"
    assert bq["target_table_name"] == "dataset.target"


@pytest.mark.parametrize("chunk_size", ["abc", "-1"])
def test_normalise_rejects_invalid_chunk_size(chunk_size: str) -> None:
    with pytest.raises(ValueError):
        session_app._normalise_form(
            {
                "source_type": "csv",
                "target_type": "csv",
                "source": "source.csv",
                "target": "target.csv",
                "chunk_size": chunk_size,
            }
        )


def test_transfer_service_can_cancel_before_full_read() -> None:
    reader = MagicMock()
    writer = MagicMock()
    service = TransferService(reader=reader, writer=writer)

    with pytest.raises(TransferCancelled):
        service.execute(
            TransferRequest(source="source.csv", target="target.csv"),
            cancel_check=lambda: True,
        )

    reader.read.assert_not_called()
    writer.close.assert_called_once()


def test_transfer_service_can_cancel_between_chunks() -> None:
    reader = MagicMock()
    reader.read_chunks.return_value = iter([
        pd.DataFrame({"id": [1]}),
        pd.DataFrame({"id": [2]}),
    ])
    writer = MagicMock()
    writer.write.return_value = 1
    service = TransferService(reader=reader, writer=writer)
    cancelled = False

    def progress_callback(**kwargs) -> None:
        nonlocal cancelled
        cancelled = True

    with pytest.raises(TransferCancelled):
        service.execute(
            TransferRequest(source="source.csv", target="target.csv", chunk_size=1),
            progress_callback=progress_callback,
            cancel_check=lambda: cancelled,
        )

    assert writer.write.call_count == 1
    writer.close.assert_called_once()
