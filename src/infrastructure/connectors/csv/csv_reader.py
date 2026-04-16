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
    def __init__(self, encoding: str = 'utf-8-sig') -> None:
        self.encoding = encoding

    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        if not os.path.exists(source):
            raise InvalidSourceError(f"Source file does not exist: {source}")

        if not source.lower().endswith('.csv'):
            raise InvalidSourceError(f"Source file is not a CSV: {source}")
        try:
            logger.debug("Reading CSV file: %s", source)
            df = pd.read_csv(source, sep=sep_file, encoding=self.encoding)
            logger.debug("CSV read complete: %d rows, %d columns", len(df), len(df.columns))
            if custom_query.strip():
                logger.debug("Applying pandas filter: %s", custom_query.strip())
                df = df.query(custom_query.strip())
                logger.debug("After filter: %d rows", len(df))
            return df
        except Exception as exc:
            logger.error("Failed to read CSV '%s': %s", source, exc)
            raise SourceReadError(f"Failed to read source file: {source}") from exc