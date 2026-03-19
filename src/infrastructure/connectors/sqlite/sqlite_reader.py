import os
import sqlite3
import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader


class SqliteReader(DataReader):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def read(self, source: str, sep_file: str = ',') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"SQLite database file not found: {source}")

        query = f"SELECT * FROM {self.table_name}"

        try:
            with sqlite3.connect(source) as connection:
                return pd.read_sql(query, connection)
        except Exception as exc:
            raise SourceReadError(
                f"Failed to read table '{self.table_name}' from SQLite source: {source}"
            ) from exc