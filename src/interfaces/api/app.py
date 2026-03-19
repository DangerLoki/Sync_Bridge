from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
 
from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import TransferError
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter
 
app = FastAPI(
    title="SyncBridge API",
    description="API para transferência de dados entre arquivos e bancos locais.",
    version="1.0.0",
)
 
templates = Jinja2Templates(directory="src/interfaces/api/templates")

app.mount("/static", StaticFiles(directory="src/interfaces/api/static"), name="static")
app.mount("/image", StaticFiles(directory="src/interfaces/api/image"), name="image")
 
 
def build_reader(source_type: str, table_name: str):
    if source_type == "csv":
        return CsvReader()
    if source_type == "sqlite":
        return SqliteReader(table_name=table_name)
    raise ValueError(f"Unsupported source type: {source_type}")
 
 
def build_writer(target_type: str, table_name: str):
    if target_type == "csv":
        return CsvWriter()
    if target_type == "sqlite":
        return SqliteWriter(table_name=table_name)
    raise ValueError(f"Unsupported target type: {target_type}")
 
 
@app.get("/health")
def health() -> dict:
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
    source: str = Form(...),
    target: str = Form(...),
    table_name: str = Form(...),
    sep_file: str = Form(','),
):
    try:
        reader = build_reader(source_type=source_type, table_name=table_name)
        writer = build_writer(target_type=target_type, table_name=table_name)
 
        service = TransferService(reader=reader, writer=writer)
        transfer_request = TransferRequest(source=source, target=target, sep_file=sep_file)
        result = service.execute(transfer_request)
 
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": result,
                "error": None,
            },
        )
    except (TransferError, ValueError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": None,
                "error": str(exc),
            },
        )