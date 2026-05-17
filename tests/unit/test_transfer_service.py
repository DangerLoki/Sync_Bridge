from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import SourceReadError, TargetWriteError
from src.domain.models.transfer_result import TransferResult


def _make_df(rows: int = 4) -> pd.DataFrame:
    return pd.DataFrame({"id": range(rows), "name": [f"name_{i}" for i in range(rows)]})


def _make_service(reader=None, writer=None):
    if reader is None:
        reader = MagicMock()
    if writer is None:
        writer = MagicMock()
    return TransferService(reader=reader, writer=writer)


class TestTransferService:
    def test_execute_returns_transfer_result(self):
        df = _make_df(4)
        reader = MagicMock()
        reader.read.return_value = df
        writer = MagicMock()
        writer.write.return_value = 4

        service = _make_service(reader, writer)
        request = TransferRequest(source="src.csv", target="tgt.db")
        result = service.execute(request)

        assert isinstance(result, TransferResult)

    def test_execute_status_is_success(self):
        df = _make_df(4)
        reader = MagicMock()
        reader.read.return_value = df
        writer = MagicMock()
        writer.write.return_value = 4

        service = _make_service(reader, writer)
        result = service.execute(TransferRequest(source="s", target="t"))

        assert result.status == "SUCCESS"

    def test_execute_rows_read_and_written_match(self):
        df = _make_df(7)
        reader = MagicMock()
        reader.read.return_value = df
        writer = MagicMock()
        writer.write.return_value = 7

        service = _make_service(reader, writer)
        result = service.execute(TransferRequest(source="s", target="t"))

        assert result.rows_read == 7
        assert result.rows_written == 7

    def test_execute_source_and_target_propagated(self):
        reader = MagicMock()
        reader.read.return_value = _make_df(1)
        writer = MagicMock()
        writer.write.return_value = 1

        service = _make_service(reader, writer)
        result = service.execute(TransferRequest(source="my_source.csv", target="my_target.db"))

        assert result.source == "my_source.csv"
        assert result.target == "my_target.db"

    def test_execute_passes_sep_file_to_reader(self):
        reader = MagicMock()
        reader.read.return_value = _make_df(2)
        writer = MagicMock()
        writer.write.return_value = 2

        service = _make_service(reader, writer)
        request = TransferRequest(source="s.csv", target="t.csv", source_sep_file=";")
        service.execute(request)

        reader.read.assert_called_once_with("s.csv", sep_file=";", custom_query="")

    def test_execute_passes_sep_file_to_writer(self):
        df = _make_df(2)
        reader = MagicMock()
        reader.read.return_value = df
        writer = MagicMock()
        writer.write.return_value = 2

        service = _make_service(reader, writer)
        request = TransferRequest(source="s.csv", target="t.csv", target_sep_file="|")
        service.execute(request)

        writer.write.assert_called_once_with(df, "t.csv", sep_file="|", append=False)

    def test_execute_passes_custom_query_to_reader(self):
        reader = MagicMock()
        reader.read.return_value = _make_df(1)
        writer = MagicMock()
        writer.write.return_value = 1

        service = _make_service(reader, writer)
        request = TransferRequest(source="s.csv", target="t.csv", custom_query="id > 2")
        service.execute(request)

        reader.read.assert_called_once_with("s.csv", sep_file=",", custom_query="id > 2")

    def test_execute_propagates_source_read_error(self):
        reader = MagicMock()
        reader.read.side_effect = SourceReadError("read failed")
        service = _make_service(reader, MagicMock())

        with pytest.raises(SourceReadError):
            service.execute(TransferRequest(source="s", target="t"))

    def test_execute_propagates_target_write_error(self):
        reader = MagicMock()
        reader.read.return_value = _make_df(2)
        writer = MagicMock()
        writer.write.side_effect = TargetWriteError("write failed")

        service = _make_service(reader, writer)
        with pytest.raises(TargetWriteError):
            service.execute(TransferRequest(source="s", target="t"))

    def test_execute_zero_rows(self):
        reader = MagicMock()
        reader.read.return_value = pd.DataFrame()
        writer = MagicMock()
        writer.write.return_value = 0

        service = _make_service(reader, writer)
        result = service.execute(TransferRequest(source="s", target="t"))

        assert result.rows_read == 0
        assert result.rows_written == 0
        assert result.status == "SUCCESS"
