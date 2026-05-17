import logging
import os
import sqlite3
from typing import Iterator

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

    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"SQLite database file not found: {source}")

        if custom_query.strip():
            query = custom_query.strip()
        else:
            query = f"SELECT * FROM {self.table_name}"

        try:
            logger.debug("Reading from SQLite '%s' — query: %s", source, query)
            with sqlite3.connect(source) as connection:
                df = pd.read_sql(query, connection)
            logger.debug("SQLite read complete: %d rows", len(df))
            return df
        except Exception as exc:
            logger.error("Failed to read table '%s' from '%s': %s", self.table_name, source, exc)
            raise SourceReadError(
                f"Failed to read table '{self.table_name}' from SQLite source: {source}"
            ) from exc

    def read_chunks(
        self,
        source: str,
        chunk_size: int,
        sep_file: str = ',',
        custom_query: str = '',
    ) -> Iterator[pd.DataFrame]:
        """Stream the SQLite query using pandas' native *chunksize* parameter."""
        if not os.path.exists(source):
            raise InvalidSourceError(f"SQLite database file not found: {source}")

        query = custom_query.strip() or f"SELECT * FROM {self.table_name}"
        try:
            logger.debug(
                "Streaming SQLite '%s' in chunks of %d rows — query: %s",
                source, chunk_size, query,
            )
            with sqlite3.connect(source) as connection:
                for chunk in pd.read_sql(query, connection, chunksize=chunk_size):
                    yield chunk
        except Exception as exc:
            logger.error(
                "Failed to stream table '%s' from '%s': %s", self.table_name, source, exc
            )
            raise SourceReadError(
                f"Failed to read table '{self.table_name}' from SQLite source: {source}"
            ) from exc