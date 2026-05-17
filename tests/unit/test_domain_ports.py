"""Tests to cover the abstract method bodies in DataReader and DataWriter ports."""
import pytest
import pandas as pd

from src.domain.ports.data_reader import DataReader
from src.domain.ports.data_writer import DataWriter


class _ConcreteReader(DataReader):
    """Subclass that delegates to super() so the abstract body is executed."""
    def read(self, source: str, sep_file: str = ',', custom_query: str = '') -> pd.DataFrame:
        return super().read(source, sep_file, custom_query)


class _ConcreteWriter(DataWriter):
    """Subclass that delegates to super() so the abstract body is executed."""
    def write(self, data: pd.DataFrame, target: str, sep_file: str = ',', append: bool = False) -> int:
        return super().write(data, target, sep_file, append)


class TestDataReaderPort:
    def test_abstract_method_raises_not_implemented(self):
        reader = _ConcreteReader()
        with pytest.raises(NotImplementedError):
            reader.read("any_source.csv")


class TestDataWriterPort:
    def test_abstract_method_raises_not_implemented(self):
        writer = _ConcreteWriter()
        df = pd.DataFrame({"col": [1, 2]})
        with pytest.raises(NotImplementedError):
            writer.write(df, "any_target.csv")
