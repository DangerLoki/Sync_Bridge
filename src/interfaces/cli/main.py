from typing import Annotated, Optional

import typer

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import TransferError
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.parquet.parquet_reader import ParquetReader
from src.infrastructure.connectors.parquet.parquet_writer import ParquetWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter

app = typer.Typer(
    name="sync-bridge",
    help="Transferência de dados tabulares entre arquivos e bancos de dados.",
    add_completion=False,
)


def _build_reader(source_type: str, table: str, encoding: str):
    if source_type == "csv":
        return CsvReader(encoding=encoding)
    if source_type == "sqlite":
        return SqliteReader(table_name=table)
    if source_type == "parquet":
        return ParquetReader()
    raise typer.BadParameter(
        f"Tipo de origem não suportado na CLI: '{source_type}'. "
        "Use a API web para SQL Server, Oracle ou BigQuery."
    )


def _build_writer(target_type: str, table: str, encoding: str, compression: str, if_exists: str):
    if target_type == "csv":
        return CsvWriter(encoding=encoding)
    if target_type == "sqlite":
        return SqliteWriter(table_name=table, if_exists=if_exists)  # type: ignore[arg-type]
    if target_type == "parquet":
        return ParquetWriter(compression=compression)  # type: ignore[arg-type]
    raise typer.BadParameter(
        f"Tipo de destino não suportado na CLI: '{target_type}'. "
        "Use a API web para SQL Server, Oracle ou BigQuery."
    )


@app.command()
def transfer(
    source: Annotated[str, typer.Argument(help="Caminho do arquivo de origem.")],
    target: Annotated[str, typer.Argument(help="Caminho do arquivo de destino.")],
    source_type: Annotated[
        str, typer.Option("--source-type", "-st", help="Tipo de origem: csv, sqlite, parquet.")
    ] = "csv",
    target_type: Annotated[
        str, typer.Option("--target-type", "-tt", help="Tipo de destino: csv, sqlite, parquet.")
    ] = "csv",
    table: Annotated[str, typer.Option(help="Nome da tabela (SQLite).")] = "data",
    sep: Annotated[str, typer.Option(help="Separador do CSV.")] = ",",
    encoding: Annotated[str, typer.Option(help="Encoding do CSV.")] = "utf-8-sig",
    compression: Annotated[
        str, typer.Option(help="Compressão Parquet: snappy, gzip, brotli, zstd.")
    ] = "snappy",
    if_exists: Annotated[
        str, typer.Option(help="Estratégia de escrita: replace ou append.")
    ] = "replace",
    query: Annotated[
        Optional[str], typer.Option(help="Consulta/filtro personalizado na leitura.")
    ] = None,
):
    """Transfere dados entre dois conectores."""
    try:
        reader = _build_reader(source_type, table, encoding)
        writer = _build_writer(target_type, table, encoding, compression, if_exists)

        request = TransferRequest(
            source=source,
            target=target,
            source_sep_file=sep,
            target_sep_file=sep,
            source_encoding=encoding,
            target_encoding=encoding,
            custom_query=query or "",
        )

        service = TransferService(reader=reader, writer=writer)
        result = service.execute(request)

        typer.secho(f"✔ {result}", fg=typer.colors.GREEN)
    except TransferError as exc:
        typer.secho(f"✘ Erro na transferência: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except typer.BadParameter as exc:
        typer.secho(f"✘ {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def demo():
    """Executa fluxos de demonstração: CSV ↔ SQLite ↔ Parquet."""
    flows = [
        ("sample_data/people.csv",
         "sample_data/app.db",
         "csv",
         "sqlite",
         "people"),
        
        ("sample_data/app.db",
         "sample_data/people_exported.csv",
         "sqlite",
         "csv",
         "people"),
        
        ("sample_data/people.csv",
         "sample_data/people.parquet",
         "csv",
         "parquet",
         ""),
        
        ("sample_data/people.parquet",
            "sample_data/people_from_parquet.csv",
            "parquet",
            "csv",
            "",),
    ]

    for src, tgt, src_type, tgt_type, table in flows:
        try:
            reader = _build_reader(src_type, table, "utf-8-sig")
            writer = _build_writer(tgt_type, table, "utf-8-sig", "snappy", "replace")
            service = TransferService(reader=reader, writer=writer)
            result = service.execute(TransferRequest(source=src, target=tgt))
            typer.secho(
                f"  ✔ {src_type} → {tgt_type}: {result.rows_written} linhas",
                fg=typer.colors.GREEN,
            )
        except TransferError as exc:
            typer.secho(f"  ✘ {src_type} → {tgt_type}: {exc}", fg=typer.colors.RED, err=True)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
