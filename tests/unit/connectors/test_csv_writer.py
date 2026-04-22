import pandas as pd
import pytest
from pathlib import Path

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.infrastructure.connectors.csv.csv_writer import CsvWriter


def _make_df() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 2, 3], "value": ["x", "y", "z"]})


class TestCsvWriter:
    def test_write_creates_csv_file(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df()

        writer = CsvWriter()
        writer.write(df, str(target))

        assert target.exists()

    def test_write_returns_row_count(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df()

        writer = CsvWriter()
        rows = writer.write(df, str(target))

        assert rows == 3

    def test_written_csv_matches_original(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df()

        writer = CsvWriter()
        writer.write(df, str(target))

        result = pd.read_csv(target, encoding="utf-8-sig")
        pd.testing.assert_frame_equal(df, result)

    def test_write_with_custom_sep(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df()

        writer = CsvWriter()
        writer.write(df, str(target), sep_file=";")

        result = pd.read_csv(target, sep=";", encoding="utf-8-sig")
        pd.testing.assert_frame_equal(df, result)

    def test_write_empty_dataframe(self, tmp_path):
        target = tmp_path / "empty.csv"
        df = pd.DataFrame(columns=["id", "value"])

        writer = CsvWriter()
        rows = writer.write(df, str(target))

        assert rows == 0
        assert target.exists()

    def test_write_raises_target_write_error_on_invalid_path(self):
        df = _make_df()
        writer = CsvWriter()

        with pytest.raises(TargetWriteError):
            writer.write(df, "/nonexistent_directory/output.csv")

    def test_write_uses_custom_encoding(self, tmp_path):
        target = tmp_path / "out.csv"
        df = pd.DataFrame({"nome": ["André", "Luís"]})

        writer = CsvWriter(encoding="latin-1")
        rows = writer.write(df, str(target))

        assert rows == 2
        result = pd.read_csv(target, encoding="latin-1")
        pd.testing.assert_frame_equal(df, result)
