#imports da biblioteca padrão
from abc import ABC, abstractmethod

#imports de bibliotecas de externas
import pandas as pd


class DataReader(ABC):
    @abstractmethod
    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        raise NotImplementedError