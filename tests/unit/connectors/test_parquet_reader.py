import pandas as pd
import pytest
from pathlib import Path

from src.domain.exceptions.transfer_exceptions import InvalidSourceError, SourceReadError
from src.infrastructure.connectors.parquet.parquet_reader import ParquetReader


def _write_parquet(path: Path) -> pd.DataFrame:
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Ana", "Bruno", "Carla"], "age": [25, 31, 28]})
    df.to_parquet(path, index=False)
    return df


class TestParquetReader:
    def test_read_returns_dataframe(self, tmp_path):
        parquet_file = tmp_path / "data.parquet"
        original = _write_parquet(parquet_file)

        reader = ParquetReader()
        df = reader.read(str(parquet_file))

        pd.testing.assert_frame_equal(original, df)

    def test_read_raises_invalid_source_when_file_not_found(self, tmp_path):
        reader = ParquetReader()
        with pytest.raises(InvalidSourceError):
            reader.read(str(tmp_path / "missing.parquet"))

    def test_read_raises_invalid_source_when_not_parquet(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,name\n1,Ana\n")

        reader = ParquetReader()
        with pytest.raises(InvalidSourceError):
            reader.read(str(csv_file))

    def test_read_with_custom_query_filters_rows(self, tmp_path):
        parquet_file = tmp_path / "data.parquet"
        _write_parquet(parquet_file)

        reader = ParquetReader()
        df = reader.read(str(parquet_file), custom_query="age > 26")

        assert len(df) == 2
        assert all(df["age"] > 26)

    def test_read_with_empty_custom_query_returns_all(self, tmp_path):
        parquet_file = tmp_path / "data.parquet"
        original = _write_parquet(parquet_file)

        reader = ParquetReader()
        df = reader.read(str(parquet_file), custom_query="  ")

        assert len(df) == len(original)

    def test_read_raises_source_read_error_on_corrupt_file(self, tmp_path):
        bad_file = tmp_path / "bad.parquet"
        bad_file.write_bytes(b"not a parquet file at all!!!")

        reader = ParquetReader()
        with pytest.raises(SourceReadError):
            reader.read(str(bad_file))
