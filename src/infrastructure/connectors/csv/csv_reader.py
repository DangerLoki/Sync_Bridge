import logging
import os
import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)

from src.domain.ports.data_reader import DataReader

logger = logging.getLogger(__name__)


class CsvReader(DataReader):
    def read(self, source: str, sep_file: str = ',') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"Source file does not exist: {source}")

        if not source.lower().endswith('.csv'):
            raise InvalidSourceError(f"Source file is not a CSV: {source}")
        try:
            logger.debug("Reading CSV file: %s", source)
            df = pd.read_csv(source, sep=sep_file)
            logger.debug("CSV read complete: %d rows, %d columns", len(df), len(df.columns))
            return df
        except Exception as exc:
            logger.error("Failed to read CSV '%s': %s", source, exc)
            raise SourceReadError(f"Failed to read source file: {source}") from exc