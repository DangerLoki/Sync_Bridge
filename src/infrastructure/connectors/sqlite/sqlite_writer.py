import sqlite3
import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter


class SqliteWriter(DataWriter):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            with sqlite3.connect(target) as connection:
                data.to_sql(self.table_name, connection, if_exists="replace", index=False)
            return len(data)
        except Exception as exc:
            raise TargetWriteError(
                f"Failed to write data to SQLite target: {target}, table: {self.table_name}"
            ) from exc