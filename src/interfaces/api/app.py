import logging
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.core.logging_config import setup_logging
from src.domain.exceptions.transfer_exceptions import TransferError
from src.infrastructure.connectors.bigquery.bigquery_reader import BigQueryReader
from src.infrastructure.connectors.bigquery.bigquery_writer import BigQueryWriter
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.oracle.oracle_reader import OracleReader
from src.infrastructure.connectors.oracle.oracle_writer import OracleWriter
from src.infrastructure.connectors.parquet.parquet_reader import ParquetReader
from src.infrastructure.connectors.parquet.parquet_writer import ParquetCompression, ParquetWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter
from src.infrastructure.connectors.sqlserver.sqlserver_reader import SqlServerReader
from src.infrastructure.connectors.sqlserver.sqlserver_writer import SqlServerWriter

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SyncBridge API",
    description="API para transferência de dados entre arquivos e bancos locais.",
    version="1.0.0",
)
 
templates = Jinja2Templates(directory="src/interfaces/api/templates")

app.mount("/static", StaticFiles(directory="src/interfaces/api/static"), name="static")
app.mount("/image", StaticFiles(directory="src/interfaces/api/image"), name="image")


def build_reader(
    source_type: str,
    table_name: str,
    encoding: str = 'utf-8-sig',
    oracle_mode: str = 'thin',
    oracle_client_dir: str = '',
    bq_project_id: str = '',
):
    if source_type == "csv":
        return CsvReader(encoding=encoding)
    if source_type == "sqlite":
        return SqliteReader(table_name=table_name)
    if source_type == "parquet":
        return ParquetReader()
    if source_type == "sqlserver":
        return SqlServerReader(table_name=table_name)
    if source_type == "oracle":
        return OracleReader(table_name=table_name,
                            mode=oracle_mode,
                            client_lib_dir=oracle_client_dir)
    if source_type == "bigquery":
        return BigQueryReader(table_name=table_name,
                              project_id=bq_project_id)
    raise ValueError(f"Unsupported source type: {source_type}")
 
 
def build_writer(
    target_type: str,
    table_name: str,
    encoding: str = 'utf-8-sig',
    compression: ParquetCompression = 'snappy',
    oracle_mode: str = 'thin',
    oracle_client_dir: str = '',
    bq_project_id: str = '',
    if_exists: str = 'replace',
):
    if target_type == "csv":
        return CsvWriter(encoding=encoding)
    if target_type == "sqlite":
        return SqliteWriter(table_name=table_name, if_exists=if_exists)  # type: ignore[arg-type]
    if target_type == "parquet":
        return ParquetWriter(compression=compression)
    if target_type == "sqlserver":
        return SqlServerWriter(table_name=table_name)
    if target_type == "oracle":
        return OracleWriter(table_name=table_name,
                            mode=oracle_mode,
                            client_lib_dir=oracle_client_dir)
    if target_type == "bigquery":
        return BigQueryWriter(table_name=table_name,
                              project_id=bq_project_id)
    raise ValueError(f"Unsupported target type: {target_type}")
 
 
@app.get("/browse")
def browse(path: str = Query(default=".")) -> JSONResponse:
    base = Path(path).resolve()
    entries = []
    try:
        items = sorted(base.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        for entry in items:
            entries.append({
                "name": entry.name,
                "path": str(entry),
                "is_dir": entry.is_dir(),
            })
    except PermissionError:
        pass
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"Path not found: {str(base)}"},
        )
    parent = str(base.parent) if base.parent != base else None
    return JSONResponse({"current": str(base), "parent": parent, "entries": entries})


@app.post("/test-connection")
def test_connection(connection_string: str = Form(...)) -> JSONResponse:
    try:
        import pyodbc
        with pyodbc.connect(connection_string, timeout=5):
            pass
        logger.info("SQL Server connection test succeeded")
        return JSONResponse({"ok": True, "message": "Conexão realizada com sucesso!"})
    except Exception as exc:
        logger.warning("SQL Server connection test failed: %s", exc)
        return JSONResponse({"ok": False, "message": str(exc)})


@app.post("/test-connection-oracle")
def test_connection_oracle(
    dsn: str = Form(...),
    mode: str = Form('thin'),
    client_lib_dir: str = Form(''),
) -> JSONResponse:
    try:
        import oracledb
        if mode == 'thick':
            try:
                oracledb.init_oracle_client(lib_dir=client_lib_dir or None)
            except Exception:
                pass  # já inicializado anteriormente
        with oracledb.connect(dsn):
            pass
        logger.info("Oracle connection test succeeded (mode=%s)", mode)
        return JSONResponse({"ok": True, "message": "Conexão Oracle realizada com sucesso!"})
    except Exception as exc:
        logger.warning("Oracle connection test failed: %s", exc)
        return JSONResponse({"ok": False, "message": str(exc)})


@app.post("/test-connection-bigquery")
def test_connection_bigquery(
    credentials_file: str = Form(...),
    project_id: str = Form(''),
) -> JSONResponse:
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        project = project_id or credentials.project_id
        client = bigquery.Client(credentials=credentials, project=project)
        # Testa listando os datasets (operação leve)
        next(iter(client.list_datasets(max_results=1)), None)
        logger.info("BigQuery connection test succeeded (project=%s)", project)
        return JSONResponse({"ok": True, "message": f"Conexão BigQuery OK — projeto: {project}"})
    except Exception as exc:
        logger.warning("BigQuery connection test failed: %s", exc)
        return JSONResponse({"ok": False, "message": str(exc)})


@app.get("/health")
def health() -> dict:
    logger.debug("Health check requested")
    return {"status": "ok"}
 
 
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "result": None,
            "error": None,
        },
    )
 
 
@app.post("/transfer", response_class=HTMLResponse)
def transfer(
    request: Request,
    source_type: str = Form(...),
    target_type: str = Form(...),
    source: str = Form(''),
    target: str = Form(''),
    source_table_name: str = Form(''),
    target_table_name: str = Form(''),
    source_sep_file: str = Form(','),
    target_sep_file: str = Form(','),
    source_encoding: str = Form('utf-8-sig'),
    target_encoding: str = Form('utf-8-sig'),
    target_compression: str = Form('snappy'),
    source_connection_string: str = Form(''),
    target_connection_string: str = Form(''),
    source_table_name_sql: str = Form(''),
    target_table_name_sql: str = Form(''),
    source_oracle_dsn: str = Form(''),
    target_oracle_dsn: str = Form(''),
    source_table_name_oracle: str = Form(''),
    target_table_name_oracle: str = Form(''),
    source_oracle_mode: str = Form('thin'),
    target_oracle_mode: str = Form('thin'),
    source_oracle_client_dir: str = Form(''),
    target_oracle_client_dir: str = Form(''),
    source_bq_credentials_file: str = Form(''),
    target_bq_credentials_file: str = Form(''),
    source_bq_project_id: str = Form(''),
    target_bq_project_id: str = Form(''),
    source_table_name_bq: str = Form(''),
    target_table_name_bq: str = Form(''),
    source_custom_query: str = Form(''),
):
    # For SQL Server, the connection string replaces the file path
    if source_type == "sqlserver" and source_connection_string:
        source = source_connection_string
    if target_type == "sqlserver" and target_connection_string:
        target = target_connection_string
    # For SQL Server, use the dedicated table name fields
    if source_type == "sqlserver":
        source_table_name = source_table_name_sql
    if target_type == "sqlserver":
        target_table_name = target_table_name_sql
    # For Oracle, DSN replaces the file path
    if source_type == "oracle" and source_oracle_dsn:
        source = source_oracle_dsn
    if target_type == "oracle" and target_oracle_dsn:
        target = target_oracle_dsn
    if source_type == "oracle":
        source_table_name = source_table_name_oracle
    if target_type == "oracle":
        target_table_name = target_table_name_oracle
    # For BigQuery, credentials file replaces the file path
    if source_type == "bigquery" and source_bq_credentials_file:
        source = source_bq_credentials_file
    if target_type == "bigquery" and target_bq_credentials_file:
        target = target_bq_credentials_file
    if source_type == "bigquery":
        source_table_name = source_table_name_bq
    if target_type == "bigquery":
        target_table_name = target_table_name_bq

    logger.info(
        "Transfer requested: %s -> %s (source_type=%s, target_type=%s)",
        source, target, source_type, target_type,
    )
    try:
        if source_type == "sqlite" and not source_table_name:
            raise ValueError("Nome da tabela é obrigatório para origens SQLite.")
        if target_type == "sqlite" and not target_table_name:
            raise ValueError("Nome da tabela é obrigatório para destinos SQLite.")
        if source_type == "sqlserver" and not source_table_name:
            raise ValueError("Nome da tabela é obrigatório para origens SQL Server.")
        if target_type == "sqlserver" and not target_table_name:
            raise ValueError("Nome da tabela é obrigatório para destinos SQL Server.")
        if source_type == "sqlserver" and not source_connection_string:
            raise ValueError("String de conexão é obrigatória para origens SQL Server.")
        if target_type == "sqlserver" and not target_connection_string:
            raise ValueError("String de conexão é obrigatória para destinos SQL Server.")
        if source_type == "oracle" and not source_oracle_dsn:
            raise ValueError("DSN é obrigatório para origens Oracle.")
        if target_type == "oracle" and not target_oracle_dsn:
            raise ValueError("DSN é obrigatório para destinos Oracle.")
        if source_type == "oracle" and not source_table_name_oracle:
            raise ValueError("Nome da tabela é obrigatório para origens Oracle.")
        if target_type == "oracle" and not target_table_name_oracle:
            raise ValueError("Nome da tabela é obrigatório para destinos Oracle.")
        if source_type == "bigquery" and not source_bq_credentials_file:
            raise ValueError("Arquivo de credenciais JSON é obrigatório para origens BigQuery.")
        if target_type == "bigquery" and not target_bq_credentials_file:
            raise ValueError("Arquivo de credenciais JSON é obrigatório para destinos BigQuery.")
        if source_type == "bigquery" and not source_table_name_bq:
            raise ValueError("Nome da tabela (dataset.tabela) é obrigatório "
                             "para origens BigQuery.")
        if target_type == "bigquery" and not target_table_name_bq:
            raise ValueError("Nome da tabela (dataset.tabela) é obrigatório "
                             "para destinos BigQuery.")

        reader = build_reader(
            source_type=source_type,
            table_name=source_table_name,
            encoding=source_encoding,
            oracle_mode=source_oracle_mode,
            oracle_client_dir=source_oracle_client_dir,
            bq_project_id=source_bq_project_id,
        )
        writer = build_writer(
            target_type=target_type,
            table_name=target_table_name,
            encoding=target_encoding,
            compression=cast(ParquetCompression, target_compression),
            oracle_mode=target_oracle_mode,
            oracle_client_dir=target_oracle_client_dir,
            bq_project_id=target_bq_project_id,
        )

        service = TransferService(reader=reader, writer=writer)
        transfer_request = TransferRequest(
            source=source,
            target=target,
            source_sep_file=source_sep_file,
            target_sep_file=target_sep_file,
            source_encoding=source_encoding,
            target_encoding=target_encoding,
            custom_query=source_custom_query,
        )
        result = service.execute(transfer_request)

        logger.info("Transfer completed: %d rows read, %d rows written",
                    result.rows_read,
                    result.rows_written)
        
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": result,
                "error": None,
            },
        )
    except (TransferError, ValueError) as exc:
        logger.error("Transfer failed: %s", exc)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": None,
                "error": str(exc),
            },
        )