import logging

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class ParquetWriter(DataWriter):
    def __init__(self, compression: str = 'snappy') -> None:
        self.compression = compression

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            logger.debug("Writing %d rows to Parquet file: %s (compression=%s)", len(data), target, self.compression)
            data.to_parquet(target, index=False, compression=self.compression)
            logger.debug("Parquet write complete: %s", target)
            return len(data)
        except Exception as exc:
            logger.error("Failed to write Parquet '%s': %s", target, exc)
            raise TargetWriteError(f"Failed to write Parquet target: {target}") from exc
