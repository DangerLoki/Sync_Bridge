
import pandas as pd
import pytest

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.infrastructure.connectors.parquet.parquet_writer import ParquetWriter


def _make_df() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "name": ["Ana", "Bruno", "Carla"]})


class TestParquetWriter:
    def test_write_creates_parquet_file(self, tmp_path):
        target = tmp_path / "out.parquet"
        writer = ParquetWriter()
        writer.write(_make_df(), str(target))

        assert target.exists()

    def test_write_returns_row_count(self, tmp_path):
        target = tmp_path / "out.parquet"
        writer = ParquetWriter()
        rows = writer.write(_make_df(), str(target))

        assert rows == 3

    def test_written_data_matches_original(self, tmp_path):
        target = tmp_path / "out.parquet"
        df = _make_df()

        writer = ParquetWriter()
        writer.write(df, str(target))

        result = pd.read_parquet(target)
        pd.testing.assert_frame_equal(df, result)

    def test_write_empty_dataframe(self, tmp_path):
        target = tmp_path / "empty.parquet"
        df = pd.DataFrame(columns=["id", "name"])

        writer = ParquetWriter()
        rows = writer.write(df, str(target))

        assert rows == 0
        assert target.exists()

    def test_write_with_snappy_compression(self, tmp_path):
        target = tmp_path / "snappy.parquet"
        df = _make_df()

        writer = ParquetWriter(compression="snappy")
        rows = writer.write(df, str(target))

        assert rows == 3
        assert pd.read_parquet(target).shape == (3, 2)

    def test_write_with_gzip_compression(self, tmp_path):
        target = tmp_path / "gzip.parquet"
        df = _make_df()

        writer = ParquetWriter(compression="gzip")
        rows = writer.write(df, str(target))

        assert rows == 3
        result = pd.read_parquet(target)
        pd.testing.assert_frame_equal(df, result)

    def test_write_raises_target_write_error_on_invalid_path(self):
        df = _make_df()
        writer = ParquetWriter()

        with pytest.raises(TargetWriteError):
            writer.write(df, "/nonexistent_dir/out.parquet")

    def test_write_with_columns_filters_columns(self, tmp_path):
        target = tmp_path / "out.parquet"
        df = _make_df()  # tem "id" e "name"

        writer = ParquetWriter(columns=["id"])
        writer.write(df, str(target))

        result = pd.read_parquet(target)
        assert list(result.columns) == ["id"]
        assert "name" not in result.columns

    def test_write_with_invalid_column_raises_error(self, tmp_path):
        target = tmp_path / "out.parquet"
        df = _make_df()

        writer = ParquetWriter(columns=["nonexistent_column"])

        with pytest.raises(TargetWriteError):
            writer.write(df, str(target))
