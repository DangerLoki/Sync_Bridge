import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter


class CsvWriter(DataWriter):
    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        try:
            data.to_csv(target, index=False, sep=sep_file)
            return len(data)
        except Exception as exc:
            raise TargetWriteError(f"Failed to write CSV target: {target}") from exc