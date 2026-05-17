#imports da biblioteca padrão
from abc import ABC, abstractmethod
from typing import Iterator

#imports de bibliotecas de externas
import pandas as pd


class DataReader(ABC):
    @abstractmethod
    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        raise NotImplementedError

    def read_chunks(
        self,
        source: str,
        chunk_size: int,
        sep_file: str = ',',
        custom_query: str = '',
    ) -> Iterator[pd.DataFrame]:
        """Yield successive chunks of *chunk_size* rows.

        The default implementation loads the full dataset and then slices it.
        Connectors should override this method to stream data natively when the
        underlying library supports it (e.g. ``pd.read_csv(chunksize=N)``).
        """
        df = self.read(source, sep_file=sep_file, custom_query=custom_query)
        if df.empty:
            yield df
            return
        for start in range(0, len(df), chunk_size):
            yield df.iloc[start : start + chunk_size]