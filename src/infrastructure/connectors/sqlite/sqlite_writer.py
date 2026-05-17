import logging
import sqlite3
from typing import Literal

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)

IfExists = Literal["replace", "append"]


class SqliteWriter(DataWriter):
    def __init__(self, table_name: str, if_exists: IfExists = "replace") -> None:
        self.table_name = table_name
        self.if_exists = if_exists

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            logger.debug(
                "Writing %d rows to SQLite table '%s' (if_exists=%s): %s",
                len(data), self.table_name, self.if_exists, target,
            )
            with sqlite3.connect(target) as connection:
                data.to_sql(self.table_name, connection, if_exists=self.if_exists, index=False)
            logger.debug("SQLite write complete: table '%s' in '%s'", self.table_name, target)
            return len(data)
        except Exception as exc:
            logger.error("Failed to write table '%s' to '%s': %s", self.table_name, target, exc)
            raise TargetWriteError(
                f"Failed to write data to SQLite target: {target}, table: {self.table_name}"
            ) from exc