import logging
from typing import Literal, cast

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class CsvWriter(DataWriter):
    def __init__(self, encoding: str = 'utf-8-sig') -> None:
        self.encoding = encoding

    def write(
        self,
        data: pd.DataFrame,
        target: str,
        sep_file: str = ',',
        append: bool = False,
    ) -> int:
        try:
            mode = cast("Literal['a', 'w']", 'a' if append else 'w')
            header = not append
            logger.debug(
                "Writing %d rows to CSV file: %s (mode=%s)", len(data), target, mode
            )
            data.to_csv(
                target,
                index=False,
                sep=sep_file,
                encoding=self.encoding,
                mode=mode,
                header=header,
            )
            logger.debug("CSV write complete: %s", target)
            return len(data)
        except Exception as exc:
            logger.error("Failed to write CSV '%s': %s", target, exc)
            raise TargetWriteError(f"Failed to write CSV target: {target}") from exc