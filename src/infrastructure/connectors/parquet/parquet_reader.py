import logging
import os
from typing import Optional

import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader

logger = logging.getLogger(__name__)


class ParquetReader(DataReader):
    def __init__(self, columns: Optional[list[str]] = None) -> None:
        self.columns = columns

    def read(self, source: str, sep_file: str = ',') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"Source file does not exist: {source}")

        if not source.lower().endswith('.parquet'):
            raise InvalidSourceError(f"Source file is not a Parquet file: {source}")

        try:
            logger.debug("Reading Parquet file: %s (columns=%s)", source, self.columns)
            df = pd.read_parquet(source, columns=self.columns)
            logger.debug("Parquet read complete: %d rows, %d columns", len(df), len(df.columns))
            return df
        except Exception as exc:
            logger.error("Failed to read Parquet '%s': %s", source, exc)
            raise SourceReadError(f"Failed to read source file: {source}") from exc
