from abc import ABC, abstractmethod
import pandas as pd

class DataReader(ABC):
    @abstractmethod
    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        raise NotImplementedError