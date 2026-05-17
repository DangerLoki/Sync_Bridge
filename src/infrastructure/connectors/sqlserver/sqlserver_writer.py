import logging
from typing import Any, cast

import pandas as pd
import pyodbc

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


def _qualify(table_name: str) -> str:
    """Envolve o nome da tabela em colchetes, respeitando schema.tabela."""
    if '.' in table_name:
        schema, table = table_name.split('.', 1)
        return f"[{schema}].[{table}]"
    return f"[{table_name}]"


class SqlServerWriter(DataWriter):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    def write(
        self,
        data: pd.DataFrame,
        target: str,
        sep_file: str = ',',
        append: bool = False,
    ) -> int:
        try:
            logger.debug(
                "Writing %d rows to SQL Server table '%s' (append=%s)",
                len(data), self.table_name, append,
            )
            with pyodbc.connect(target) as connection:
                cursor = connection.cursor()
                # Bulk copy mode: sends all rows in a single TDS batch instead of
                # one RPC call per row. Equivalent to using the BCP protocol.
                cursor.fast_executemany = True

                qualified = _qualify(self.table_name)

                if not append:
                    # Drop and recreate table to match "replace" behavior
                    cursor.execute(
                        f"IF OBJECT_ID(N'{qualified}', N'U') IS NOT NULL "
                        f"DROP TABLE {qualified}"
                    )

                    # Build CREATE TABLE from DataFrame dtypes
                    col_defs = []
                    for col_name, dtype in data.dtypes.items():
                        if pd.api.types.is_integer_dtype(dtype):
                            sql_type = "BIGINT"
                        elif pd.api.types.is_float_dtype(dtype):
                            sql_type = "FLOAT"
                        elif pd.api.types.is_bool_dtype(dtype):
                            sql_type = "BIT"
                        elif pd.api.types.is_datetime64_any_dtype(dtype):
                            sql_type = "DATETIME2"
                        else:
                            sql_type = "NVARCHAR(MAX)"
                        col_defs.append(f"[{col_name}] {sql_type}")

                    create_sql = f"CREATE TABLE {qualified} ({', '.join(col_defs)})"
                    cursor.execute(create_sql)

                # Insert rows in batches using parameterized queries
                if not data.empty:
                    placeholders = ", ".join(["?"] * len(data.columns))
                    insert_sql = f"INSERT INTO {qualified} VALUES ({placeholders})"

                    # Convert to object dtype first so that replacing NaN/NaT with None
                    # produces Python None (not numpy nan), which pyodbc sends as NULL.
                    # Using only pd.notna().where() on float64 columns keeps the float
                    # dtype and itertuples still yields float('nan'), causing error 8023.
                    clean = data.astype(object).where(
                        pd.notna(data),
                        other=cast(Any, None)  # type: ignore[assignment]
                    )

                    batch_size = 10000
                    rows = [tuple(row) for row in clean.itertuples(index=False, name=None)]
                    for i in range(0, len(rows), batch_size):
                        cursor.executemany(insert_sql, rows[i:i + batch_size])

                connection.commit()

            logger.debug("SQL Server write complete: table '%s'", self.table_name)
            return len(data)
        except pyodbc.Error as exc:
            logger.error("Failed to write table '%s' to SQL Server: %s", self.table_name, exc)
            raise TargetWriteError(
                f"Failed to write data to SQL Server table '{self.table_name}': {exc}"
            ) from exc
