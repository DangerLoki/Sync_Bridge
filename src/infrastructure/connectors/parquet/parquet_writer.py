import logging
from typing import Optional

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class ParquetWriter(DataWriter):
    def __init__(self, columns: Optional[list[str]] = None) -> None:
        self.columns = columns

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            df = data[self.columns] if self.columns else data
            logger.debug("Writing %d rows to Parquet file: %s (columns=%s)", len(df), target, self.columns)
            df.to_parquet(target, index=False)
            logger.debug("Parquet write complete: %s", target)
            return len(df)
        except Exception as exc:
            logger.error("Failed to write Parquet '%s': %s", target, exc)
            raise TargetWriteError(f"Failed to write Parquet target: {target}") from exc
