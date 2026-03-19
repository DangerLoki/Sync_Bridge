import logging

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class CsvWriter(DataWriter):
    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            logger.debug("Writing %d rows to CSV file: %s", len(data), target)
            data.to_csv(target, index=False, sep=sep_file)
            logger.debug("CSV write complete: %s", target)
            return len(data)
        except Exception as exc:
            logger.error("Failed to write CSV '%s': %s", target, exc)
            raise TargetWriteError(f"Failed to write CSV target: {target}") from exc