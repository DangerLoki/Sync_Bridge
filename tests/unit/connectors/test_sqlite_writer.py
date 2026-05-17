import sqlite3

import pandas as pd

from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter


def _make_df() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Ana", "Bruno", "Carla"]})


class TestSqliteWriter:
    def test_write_creates_db_file(self, tmp_path):
        db = tmp_path / "out.db"
        writer = SqliteWriter(table_name="people")
        writer.write(_make_df(), str(db))

        assert db.exists()

    def test_write_returns_row_count(self, tmp_path):
        db = tmp_path / "out.db"
        writer = SqliteWriter(table_name="people")
        rows = writer.write(_make_df(), str(db))

        assert rows == 3

    def test_written_data_is_readable_from_db(self, tmp_path):
        db = tmp_path / "out.db"
        df = _make_df()

        writer = SqliteWriter(table_name="people")
        writer.write(df, str(db))

        with sqlite3.connect(db) as conn:
            result = pd.read_sql("SELECT * FROM people", conn)

        pd.testing.assert_frame_equal(df, result)

    def test_write_replaces_existing_table(self, tmp_path):
        db = tmp_path / "out.db"
        df_old = pd.DataFrame({"id": [10, 20], "name": ["X", "Y"]})
        df_new = _make_df()

        writer = SqliteWriter(table_name="people")
        writer.write(df_old, str(db))
        writer.write(df_new, str(db))

        with sqlite3.connect(db) as conn:
            result = pd.read_sql("SELECT * FROM people", conn)

        pd.testing.assert_frame_equal(df_new, result)

    def test_write_empty_dataframe(self, tmp_path):
        db = tmp_path / "out.db"
        df = pd.DataFrame(columns=["id", "name"])

        writer = SqliteWriter(table_name="people")
        rows = writer.write(df, str(db))

        assert rows == 0

    def test_write_different_table_names(self, tmp_path):
        db = tmp_path / "out.db"
        df = _make_df()

        SqliteWriter(table_name="table_a").write(df, str(db))
        SqliteWriter(table_name="table_b").write(df, str(db))

        with sqlite3.connect(db) as conn:
            tables = pd.read_sql(
                "SELECT name FROM sqlite_master WHERE type='table'", conn
            )

        assert "table_a" in tables["name"].values
        assert "table_b" in tables["name"].values
