import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import InvalidSourceError
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter


def create_sample_csv(file_path: Path) -> pd.DataFrame:
    print(f"Creating sample CSV at: {file_path}")
    df = pd.DataFrame(
        [
            {"id": 1, "name": "Ana", "age": 25, "city": "Sao Paulo"},
            {"id": 2, "name": "Bruno", "age": 31, "city": "Rio de Janeiro"},
            {"id": 3, "name": "Carla", "age": 28, "city": "Belo Horizonte"},
            {"id": 4, "name": "Diego", "age": 35, "city": "Curitiba"},
        ]
    )
    df.to_csv(file_path, index=False)
    return df


def test_csv_to_sqlite_success(tmp_path: Path) -> None:
    print(f"Testing CSV to SQLite transfer with temporary path: {tmp_path}")

    source_csv = tmp_path / "people.csv"
    target_db = tmp_path / "app.db"
    table_name = "people"

    original_df = create_sample_csv(source_csv)

    reader = CsvReader()
    writer = SqliteWriter(table_name=table_name)
    service = TransferService(reader=reader, writer=writer)

    request = TransferRequest(source=str(source_csv), target=str(target_db))
    result = service.execute(request)

    assert result.status == "SUCCESS"
    assert result.rows_read == 4
    assert result.rows_written == 4

    with sqlite3.connect(target_db) as conn:
        db_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)

    pd.testing.assert_frame_equal(original_df, db_df)


def test_sqlite_to_csv_success(tmp_path: Path) -> None:
    print(f"Testing SQLite to CSV transfer with temporary path: {tmp_path}")

    source_db = tmp_path / "app.db"
    target_csv = tmp_path / "people_exported.csv"
    table_name = "people"

    original_df = pd.DataFrame(
        [
            {"id": 1, "name": "Ana", "age": 25, "city": "Sao Paulo"},
            {"id": 2, "name": "Bruno", "age": 31, "city": "Rio de Janeiro"},
            {"id": 3, "name": "Carla", "age": 28, "city": "Belo Horizonte"},
            {"id": 4, "name": "Diego", "age": 35, "city": "Curitiba"},
        ]
    )

    with sqlite3.connect(source_db) as conn:
        original_df.to_sql(table_name, conn, if_exists="replace", index=False)

    reader = SqliteReader(table_name=table_name)
    writer = CsvWriter()
    service = TransferService(reader=reader, writer=writer)

    request = TransferRequest(source=str(source_db), target=str(target_csv))
    result = service.execute(request)

    assert result.status == "SUCCESS"
    assert result.rows_read == 4
    assert result.rows_written == 4

    exported_df = pd.read_csv(target_csv)
    pd.testing.assert_frame_equal(original_df, exported_df)


def test_csv_reader_raises_error_when_file_does_not_exist(tmp_path: Path) -> None:
    print(f"Testing CSV reader error handling with temporary path: {tmp_path}")
    
    missing_csv = tmp_path / "missing.csv"
    target_db = tmp_path / "app.db"

    reader = CsvReader()
    writer = SqliteWriter(table_name="people")
    service = TransferService(reader=reader, writer=writer)

    request = TransferRequest(source=str(missing_csv), target=str(target_db))

    with pytest.raises(InvalidSourceError):
        service.execute(request)