from abc import ABC, abstractmethod
import pandas as pd


class DataWriter(ABC):
    @abstractmethod
    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',') -> int:
        """Write a DataFrame to a target and return number of rows written."""
        raise NotImplementedError