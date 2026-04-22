import sqlite3
import pandas as pd
import pytest
from pathlib import Path

from src.domain.exceptions.transfer_exceptions import InvalidSourceError, SourceReadError
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader


def _create_db(db_path: Path, table_name: str = "people") -> pd.DataFrame:
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Ana", "Bruno", "Carla"]})
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    return df


class TestSqliteReader:
    def test_read_returns_dataframe(self, tmp_path):
        db = tmp_path / "app.db"
        original = _create_db(db)

        reader = SqliteReader(table_name="people")
        df = reader.read(str(db))

        pd.testing.assert_frame_equal(original, df)

    def test_read_raises_invalid_source_when_db_not_found(self, tmp_path):
        reader = SqliteReader(table_name="people")
        with pytest.raises(InvalidSourceError):
            reader.read(str(tmp_path / "missing.db"))

    def test_read_with_custom_query(self, tmp_path):
        db = tmp_path / "app.db"
        _create_db(db)

        reader = SqliteReader(table_name="people")
        df = reader.read(str(db), custom_query="SELECT * FROM people WHERE id > 1")

        assert len(df) == 2
        assert all(df["id"] > 1)

    def test_read_without_custom_query_selects_all(self, tmp_path):
        db = tmp_path / "app.db"
        original = _create_db(db)

        reader = SqliteReader(table_name="people")
        df = reader.read(str(db))

        assert len(df) == len(original)

    def test_read_raises_source_read_error_on_bad_query(self, tmp_path):
        db = tmp_path / "app.db"
        _create_db(db)

        reader = SqliteReader(table_name="people")
        with pytest.raises(SourceReadError):
            reader.read(str(db), custom_query="SELECT * FROM nonexistent_table")

    def test_read_raises_source_read_error_on_missing_table(self, tmp_path):
        db = tmp_path / "empty.db"
        # Create empty db (no tables)
        with sqlite3.connect(db) as conn:
            pass

        reader = SqliteReader(table_name="missing_table")
        with pytest.raises(SourceReadError):
            reader.read(str(db))
