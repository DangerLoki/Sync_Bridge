import logging
import os
import sqlite3
import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader

logger = logging.getLogger(__name__)


class SqliteReader(DataReader):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def read(self, source: str, sep_file: str = ',') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"SQLite database file not found: {source}")

        query = f"SELECT * FROM {self.table_name}"

        try:
            logger.debug("Reading table '%s' from SQLite: %s", self.table_name, source)
            with sqlite3.connect(source) as connection:
                df = pd.read_sql(query, connection)
            logger.debug("SQLite read complete: %d rows from '%s'", len(df), self.table_name)
            return df
        except Exception as exc:
            logger.error("Failed to read table '%s' from '%s': %s", self.table_name, source, exc)
            raise SourceReadError(
                f"Failed to read table '{self.table_name}' from SQLite source: {source}"
            ) from exc