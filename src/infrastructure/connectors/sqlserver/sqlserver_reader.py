import logging

import pandas as pd
import pyodbc

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader

logger = logging.getLogger(__name__)


def _qualify(table_name: str) -> str:
    if '.' in table_name:
        schema, table = table_name.split('.', 1)
        return f"[{schema}].[{table}]"
    return f"[{table_name}]"


class SqlServerReader(DataReader):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        if not source:
            raise InvalidSourceError("SQL Server connection string is required.")

        if custom_query.strip():
            query = custom_query.strip()
        else:
            query = f"SELECT * FROM {_qualify(self.table_name)}"

        try:
            logger.debug("Reading from SQL Server — query: %s", query)
            with pyodbc.connect(source) as connection:
                df = pd.read_sql(query, connection)
            logger.debug("SQL Server read complete: %d rows", len(df))
            return df
        except pyodbc.Error as exc:
            logger.error("Failed to read table '%s' from SQL Server: %s", self.table_name, exc)
            raise SourceReadError(
                f"Failed to read table '{self.table_name}' from SQL Server: {exc}"
            ) from exc
