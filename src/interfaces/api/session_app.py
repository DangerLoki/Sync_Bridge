"""Web app extensions for persistent transfer jobs and cooperative cancellation.

This module imports the existing FastAPI application and adds a server-side job
registry.  A transfer is no longer tied to the lifetime of the browser's SSE
request, so refreshing the page can reconnect to the same running job.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import TransferCancelled
from src.infrastructure.connectors.parquet.parquet_writer import ParquetCompression
from src.interfaces.api.app import app, build_reader, build_writer

logger = logging.getLogger(__name__)

_TERMINAL_STATUSES = {"done", "cancelled", "error"}
_MAX_EVENTS_PER_JOB = 5000
_MAX_RETAINED_JOBS = 50


@dataclass
class TransferJob:
    job_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    status: str = "running"
    source: str = ""
    target: str = ""
    rows_read: int = 0
    rows_written: int = 0
    error: str | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    events: list[dict[str, Any]] = field(default_factory=list)
    next_event_id: int = 1
    lock: threading.RLock = field(default_factory=threading.RLock)
    thread_ident: int | None = None

    def publish(self, event: dict[str, Any]) -> None:
        with self.lock:
            item = dict(event)
            item["id"] = self.next_event_id
            self.next_event_id += 1
            self.events.append(item)
            if len(self.events) > _MAX_EVENTS_PER_JOB:
                del self.events[: len(self.events) - _MAX_EVENTS_PER_JOB]

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "source": self.source,
                "target": self.target,
                "rows_read": self.rows_read,
                "rows_written": self.rows_written,
                "error": self.error,
                "created_at": self.created_at.isoformat(),
                "finished_at": self.finished_at.isoformat() if self.finished_at else None,
                "can_cancel": self.status in {"running", "cancelling"},
                "last_event_id": self.next_event_id - 1,
            }


_jobs: dict[str, TransferJob] = {}
_jobs_lock = threading.RLock()


def _get_job(job_id: str) -> TransferJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def _cleanup_jobs() -> None:
    """Keep bounded in-memory history while never removing active jobs."""
    with _jobs_lock:
        if len(_jobs) <= _MAX_RETAINED_JOBS:
            return
        completed = sorted(
            (job for job in _jobs.values() if job.status in _TERMINAL_STATUSES),
            key=lambda job: job.finished_at or job.created_at,
        )
        while len(_jobs) > _MAX_RETAINED_JOBS and completed:
            old = completed.pop(0)
            _jobs.pop(old.job_id, None)


def _form_text(form: Any, key: str, default: str = "") -> str:
    value = form.get(key, default)
    return str(value) if value is not None else default


def _normalise_form(form: Any) -> dict[str, Any]:
    source_type = _form_text(form, "source_type")
    target_type = _form_text(form, "target_type")
    source = _form_text(form, "source")
    target = _form_text(form, "target")
    source_table_name = _form_text(form, "source_table_name")
    target_table_name = _form_text(form, "target_table_name")

    source_connection_string = _form_text(form, "source_connection_string")
    target_connection_string = _form_text(form, "target_connection_string")
    source_table_name_sql = _form_text(form, "source_table_name_sql")
    target_table_name_sql = _form_text(form, "target_table_name_sql")

    source_oracle_dsn = _form_text(form, "source_oracle_dsn")
    target_oracle_dsn = _form_text(form, "target_oracle_dsn")
    source_table_name_oracle = _form_text(form, "source_table_name_oracle")
    target_table_name_oracle = _form_text(form, "target_table_name_oracle")

    source_bq_credentials_file = _form_text(form, "source_bq_credentials_file")
    target_bq_credentials_file = _form_text(form, "target_bq_credentials_file")
    source_table_name_bq = _form_text(form, "source_table_name_bq")
    target_table_name_bq = _form_text(form, "target_table_name_bq")

    if source_type == "sqlserver":
        source = source_connection_string
        source_table_name = source_table_name_sql
    if target_type == "sqlserver":
        target = target_connection_string
        target_table_name = target_table_name_sql
    if source_type == "oracle":
        source = source_oracle_dsn
        source_table_name = source_table_name_oracle
    if target_type == "oracle":
        target = target_oracle_dsn
        target_table_name = target_table_name_oracle
    if source_type == "bigquery":
        source = source_bq_credentials_file
        source_table_name = source_table_name_bq
    if target_type == "bigquery":
        target = target_bq_credentials_file
        target_table_name = target_table_name_bq

    required = [
        (source_type == "sqlite" and not source_table_name,
         "Nome da tabela é obrigatório para origens SQLite."),
        (target_type == "sqlite" and not target_table_name,
         "Nome da tabela é obrigatório para destinos SQLite."),
        (source_type == "sqlserver" and not source_connection_string,
         "String de conexão é obrigatória para origens SQL Server."),
        (target_type == "sqlserver" and not target_connection_string,
         "String de conexão é obrigatória para destinos SQL Server."),
        (source_type == "sqlserver" and not source_table_name,
         "Nome da tabela é obrigatório para origens SQL Server."),
        (target_type == "sqlserver" and not target_table_name,
         "Nome da tabela é obrigatório para destinos SQL Server."),
        (source_type == "oracle" and not source_oracle_dsn,
         "DSN é obrigatório para origens Oracle."),
        (target_type == "oracle" and not target_oracle_dsn,
         "DSN é obrigatório para destinos Oracle."),
        (source_type == "oracle" and not source_table_name,
         "Nome da tabela é obrigatório para origens Oracle."),
        (target_type == "oracle" and not target_table_name,
         "Nome da tabela é obrigatório para destinos Oracle."),
        (source_type == "bigquery" and not source_bq_credentials_file,
         "Arquivo de credenciais JSON é obrigatório para origens BigQuery."),
        (target_type == "bigquery" and not target_bq_credentials_file,
         "Arquivo de credenciais JSON é obrigatório para destinos BigQuery."),
        (source_type == "bigquery" and not source_table_name,
         "Nome da tabela (dataset.tabela) é obrigatório para origens BigQuery."),
        (target_type == "bigquery" and not target_table_name,
         "Nome da tabela (dataset.tabela) é obrigatório para destinos BigQuery."),
    ]
    for invalid, message in required:
        if invalid:
            raise ValueError(message)

    try:
        chunk_size = int(_form_text(form, "chunk_size", "0") or "0")
    except ValueError as exc:
        raise ValueError("Tamanho do chunk deve ser um número inteiro.") from exc
    if chunk_size < 0:
        raise ValueError("Tamanho do chunk não pode ser negativo.")

    return {
        "source_type": source_type,
        "target_type": target_type,
        "source": source,
        "target": target,
        "source_table_name": source_table_name,
        "target_table_name": target_table_name,
        "source_sep_file": _form_text(form, "source_sep_file", ","),
        "target_sep_file": _form_text(form, "target_sep_file", ","),
        "source_encoding": _form_text(form, "source_encoding", "utf-8-sig"),
        "target_encoding": _form_text(form, "target_encoding", "utf-8-sig"),
        "target_compression": _form_text(form, "target_compression", "snappy"),
        "source_oracle_mode": _form_text(form, "source_oracle_mode", "thin"),
        "target_oracle_mode": _form_text(form, "target_oracle_mode", "thin"),
        "source_oracle_client_dir": _form_text(form, "source_oracle_client_dir"),
        "target_oracle_client_dir": _form_text(form, "target_oracle_client_dir"),
        "source_bq_project_id": _form_text(form, "source_bq_project_id"),
        "target_bq_project_id": _form_text(form, "target_bq_project_id"),
        "source_custom_query": _form_text(form, "source_custom_query"),
        "chunk_size": chunk_size,
    }


def _run_job(job: TransferJob, config: dict[str, Any]) -> None:
    job.thread_ident = threading.get_ident()

    class _JobLogHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
            if record.thread != job.thread_ident:
                return
            try:
                job.publish({
                    "type": "log",
                    "level": record.levelname.lower(),
                    "msg": self.format(record),
                })
            except Exception:
                pass

    handler = _JobLogHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(name)s — %(message)s"))
    root_log = logging.getLogger()
    root_log.addHandler(handler)

    try:
        job.source = config["source"]
        job.target = config["target"]
        job.publish({
            "type": "start",
            "msg": f"Iniciando transferência: {job.source} → {job.target}",
        })

        reader = build_reader(
            source_type=config["source_type"],
            table_name=config["source_table_name"],
            encoding=config["source_encoding"],
            oracle_mode=config["source_oracle_mode"],
            oracle_client_dir=config["source_oracle_client_dir"],
            bq_project_id=config["source_bq_project_id"],
        )
        writer = build_writer(
            target_type=config["target_type"],
            table_name=config["target_table_name"],
            encoding=config["target_encoding"],
            compression=cast(ParquetCompression, config["target_compression"]),
            oracle_mode=config["target_oracle_mode"],
            oracle_client_dir=config["target_oracle_client_dir"],
            bq_project_id=config["target_bq_project_id"],
        )
        service = TransferService(reader=reader, writer=writer)
        transfer_request = TransferRequest(
            source=config["source"],
            target=config["target"],
            source_sep_file=config["source_sep_file"],
            target_sep_file=config["target_sep_file"],
            source_encoding=config["source_encoding"],
            target_encoding=config["target_encoding"],
            custom_query=config["source_custom_query"],
            chunk_size=config["chunk_size"],
        )

        def _on_progress(
            rows_read: int,
            rows_written: int,
            chunk_index: int,
            done: bool,
        ) -> None:
            with job.lock:
                job.rows_read = rows_read
                job.rows_written = rows_written
            job.publish({
                "type": "progress",
                "rows_read": rows_read,
                "rows_written": rows_written,
                "chunk_index": chunk_index,
                "done": done,
            })

        result = service.execute(
            transfer_request,
            progress_callback=_on_progress,
            cancel_check=job.cancel_event.is_set,
        )
        with job.lock:
            job.rows_read = result.rows_read
            job.rows_written = result.rows_written
            job.status = "done"
        job.publish({
            "type": "done",
            "rows_read": result.rows_read,
            "rows_written": result.rows_written,
            "source": result.source,
            "target": result.target,
            "status": result.status,
        })

    except TransferCancelled as exc:
        with job.lock:
            job.status = "cancelled"
        job.publish({
            "type": "cancelled",
            "msg": str(exc),
            "rows_read": job.rows_read,
            "rows_written": job.rows_written,
            "partial_output": job.rows_written > 0,
        })
        logger.info("Transfer job %s cancelled", job.job_id)

    except Exception as exc:
        logger.error("Transfer job %s failed: %s", job.job_id, exc, exc_info=True)
        with job.lock:
            job.status = "error"
            job.error = str(exc)
        job.publish({"type": "error", "msg": str(exc)})

    finally:
        root_log.removeHandler(handler)
        with job.lock:
            job.finished_at = datetime.now(UTC)
        _cleanup_jobs()


@app.post("/transfer/jobs")
async def create_transfer_job(request: Request) -> JSONResponse:
    try:
        form = await request.form()
        config = _normalise_form(form)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    job = TransferJob(
        job_id=uuid.uuid4().hex,
        source=config["source"],
        target=config["target"],
    )
    with _jobs_lock:
        _jobs[job.job_id] = job
    _cleanup_jobs()

    thread = threading.Thread(
        target=_run_job,
        args=(job, config),
        name=f"syncbridge-job-{job.job_id[:8]}",
        daemon=True,
    )
    thread.start()

    return JSONResponse({"job_id": job.job_id, "status": job.status})


@app.get("/transfer/jobs/{job_id}")
def get_transfer_job(job_id: str) -> JSONResponse:
    job = _get_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Execução não encontrada."})
    return JSONResponse(job.snapshot())


@app.post("/transfer/jobs/{job_id}/cancel")
def cancel_transfer_job(job_id: str) -> JSONResponse:
    job = _get_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Execução não encontrada."})

    with job.lock:
        if job.status in _TERMINAL_STATUSES:
            return JSONResponse({
                "job_id": job.job_id,
                "status": job.status,
                "accepted": False,
            })
        if job.status != "cancelling":
            job.status = "cancelling"
            job.cancel_event.set()
            job.publish({
                "type": "cancel_requested",
                "msg": "Cancelamento solicitado. Aguardando o ponto seguro mais próximo.",
            })

    return JSONResponse({
        "job_id": job.job_id,
        "status": job.status,
        "accepted": True,
    })


@app.get("/transfer/jobs/{job_id}/stream")
async def stream_transfer_job(
    request: Request,
    job_id: str,
    after: int = 0,
) -> Response:
    job = _get_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Execução não encontrada."})

    last_event_header = request.headers.get("last-event-id", "").strip()
    if last_event_header.isdigit():
        after = max(after, int(last_event_header))

    async def _generate():
        nonlocal after
        last_keepalive = time.monotonic()

        while True:
            with job.lock:
                pending = [event for event in job.events if int(event["id"]) > after]
                terminal = job.status in _TERMINAL_STATUSES

            if pending:
                for event in pending:
                    after = int(event["id"])
                    yield f"id: {after}\n"
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                last_keepalive = time.monotonic()
                continue

            if terminal:
                break

            if await request.is_disconnected():
                break

            if time.monotonic() - last_keepalive >= 15:
                yield ": keepalive\n\n"
                last_keepalive = time.monotonic()

            await asyncio.sleep(0.35)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


_SESSION_SCRIPT = b'<script src="/static/session.js?v=1"></script>\n'


@app.middleware("http")
async def inject_session_script(request: Request, call_next):
    """Load the persistence layer without rewriting the existing large template."""
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    if b"/static/session.js" not in body:
        body = body.replace(b"</body>", _SESSION_SCRIPT + b"</body>")

    headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() != "content-length"
    }
    return Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        background=response.background,
    )
