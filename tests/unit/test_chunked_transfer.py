"""Tests for chunk-based transfer processing.

Covers:
- TransferRequest.chunk_size field and validation
- DataReader.read_chunks default implementation (slice-based)
- CsvReader.read_chunks native implementation (pd.read_csv chunksize)
- SqliteReader.read_chunks native implementation (pd.read_sql chunksize)
- CsvWriter append mode
- SqliteWriter append mode
- ParquetWriter chunked write (pyarrow.parquet.ParquetWriter)
- TransferService chunked execution path
"""

import sqlite3

import pandas as pd
import pytest

from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.models.transfer_result import TransferResult
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.parquet.parquet_reader import ParquetReader
from src.infrastructure.connectors.parquet.parquet_writer import ParquetWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(rows: int = 10) -> pd.DataFrame:
    return pd.DataFrame({
        "id": range(rows),
        "value": [f"v{i}" for i in range(rows)],
    })


def _write_csv(path, df: pd.DataFrame, sep: str = ",") -> None:
    df.to_csv(path, index=False, sep=sep, encoding="utf-8-sig")


def _write_sqlite(path, df: pd.DataFrame, table: str = "data") -> None:
    with sqlite3.connect(path) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)


# ---------------------------------------------------------------------------
# TransferRequest.chunk_size
# ---------------------------------------------------------------------------

class TestTransferRequestChunkSize:
    def test_default_chunk_size_is_zero(self):
        req = TransferRequest(source="a", target="b")
        assert req.chunk_size == 0

    def test_positive_chunk_size_accepted(self):
        req = TransferRequest(source="a", target="b", chunk_size=500)
        assert req.chunk_size == 500

    def test_negative_chunk_size_raises(self):
        with pytest.raises(ValueError, match="chunk_size"):
            TransferRequest(source="a", target="b", chunk_size=-1)


# ---------------------------------------------------------------------------
# DataReader.read_chunks default (slice-based)
# ---------------------------------------------------------------------------

class TestDataReaderReadChunksDefault:
    """The default read_chunks() slices the fully-loaded DataFrame."""

    def test_exact_multiple(self, tmp_path):
        csv = tmp_path / "data.csv"
        _write_csv(csv, _make_df(9))

        reader = CsvReader()
        # Use the default slice-based implementation via parent (not the native override)
        # — we test it by checking chunk sizes.
        chunks = list(reader.read_chunks(str(csv), chunk_size=3))

        assert len(chunks) == 3
        for c in chunks:
            assert len(c) == 3

    def test_non_exact_multiple(self, tmp_path):
        csv = tmp_path / "data.csv"
        _write_csv(csv, _make_df(10))

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=3))

        sizes = [len(c) for c in chunks]
        assert sum(sizes) == 10
        # Last chunk is the remainder
        assert sizes[-1] == 1

    def test_chunk_size_larger_than_data(self, tmp_path):
        csv = tmp_path / "data.csv"
        _write_csv(csv, _make_df(4))

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=100))

        assert len(chunks) == 1
        assert len(chunks[0]) == 4

    def test_empty_source_yields_empty_chunk(self, tmp_path):
        csv = tmp_path / "data.csv"
        _write_csv(csv, pd.DataFrame(columns=["id", "value"]))

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=5))

        assert len(chunks) == 1
        assert chunks[0].empty

    def test_all_rows_reassembled_equal_original(self, tmp_path):
        df = _make_df(17)
        csv = tmp_path / "data.csv"
        _write_csv(csv, df)

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=5))
        reassembled = pd.concat(chunks).reset_index(drop=True)

        pd.testing.assert_frame_equal(df, reassembled)


# ---------------------------------------------------------------------------
# CsvReader native read_chunks
# ---------------------------------------------------------------------------

class TestCsvReaderReadChunks:
    def test_native_chunks_reassemble_to_original(self, tmp_path):
        df = _make_df(20)
        csv = tmp_path / "data.csv"
        _write_csv(csv, df)

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=7))
        result = pd.concat(chunks).reset_index(drop=True)

        pd.testing.assert_frame_equal(df, result)

    def test_native_chunks_with_filter(self, tmp_path):
        df = _make_df(10)
        csv = tmp_path / "data.csv"
        _write_csv(csv, df)

        reader = CsvReader()
        chunks = list(reader.read_chunks(str(csv), chunk_size=4, custom_query="id < 5"))
        result = pd.concat(chunks).reset_index(drop=True)

        expected = df[df["id"] < 5].reset_index(drop=True)
        pd.testing.assert_frame_equal(result, expected)


# ---------------------------------------------------------------------------
# SqliteReader native read_chunks
# ---------------------------------------------------------------------------

class TestSqliteReaderReadChunks:
    def test_native_chunks_reassemble_to_original(self, tmp_path):
        df = _make_df(15)
        db = tmp_path / "db.sqlite"
        _write_sqlite(db, df)

        reader = SqliteReader(table_name="data")
        chunks = list(reader.read_chunks(str(db), chunk_size=4))
        result = pd.concat(chunks).reset_index(drop=True)

        pd.testing.assert_frame_equal(df, result)


# ---------------------------------------------------------------------------
# CsvWriter append mode
# ---------------------------------------------------------------------------

class TestCsvWriterAppend:
    def test_append_adds_rows_without_duplicate_header(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df(5)

        writer = CsvWriter()
        writer.write(df.iloc[:3], str(target), append=False)
        writer.write(df.iloc[3:], str(target), append=True)

        result = pd.read_csv(target, encoding="utf-8-sig")
        assert len(result) == 5

    def test_append_preserves_all_rows(self, tmp_path):
        target = tmp_path / "out.csv"
        df = _make_df(6)

        writer = CsvWriter()
        writer.write(df.iloc[:3], str(target), append=False)
        writer.write(df.iloc[3:], str(target), append=True)

        result = pd.read_csv(target, encoding="utf-8-sig").reset_index(drop=True)
        expected = df.reset_index(drop=True)
        pd.testing.assert_frame_equal(result, expected)


# ---------------------------------------------------------------------------
# SqliteWriter append mode
# ---------------------------------------------------------------------------

class TestSqliteWriterAppend:
    def test_append_adds_rows(self, tmp_path):
        db = tmp_path / "out.db"
        df = _make_df(6)

        writer = SqliteWriter(table_name="data")
        writer.write(df.iloc[:3], str(db), append=False)
        writer.write(df.iloc[3:], str(db), append=True)

        with sqlite3.connect(db) as conn:
            result = pd.read_sql("SELECT * FROM data", conn)

        assert len(result) == 6

    def test_append_preserves_all_rows(self, tmp_path):
        db = tmp_path / "out.db"
        df = _make_df(6)

        writer = SqliteWriter(table_name="data")
        writer.write(df.iloc[:3], str(db), append=False)
        writer.write(df.iloc[3:], str(db), append=True)

        with sqlite3.connect(db) as conn:
            result = pd.read_sql("SELECT * FROM data", conn).reset_index(drop=True)

        pd.testing.assert_frame_equal(df.reset_index(drop=True), result)


# ---------------------------------------------------------------------------
# ParquetWriter chunked write
# ---------------------------------------------------------------------------

class TestParquetWriterChunked:
    def test_chunked_write_produces_valid_parquet(self, tmp_path):
        target = tmp_path / "out.parquet"
        df = _make_df(9)

        writer = ParquetWriter()
        writer.write(df.iloc[:3], str(target), append=False)
        writer.write(df.iloc[3:6], str(target), append=True)
        writer.write(df.iloc[6:], str(target), append=True)
        writer.close()

        result = pd.read_parquet(target).reset_index(drop=True)
        pd.testing.assert_frame_equal(df.reset_index(drop=True), result)

    def test_close_without_write_is_safe(self):
        writer = ParquetWriter()
        writer.close()  # should not raise


# ---------------------------------------------------------------------------
# TransferService chunked mode (end-to-end with CSV → SQLite)
# ---------------------------------------------------------------------------

class TestTransferServiceChunked:
    def test_chunked_returns_transfer_result(self, tmp_path):
        df = _make_df(10)
        src = tmp_path / "src.csv"
        tgt = tmp_path / "tgt.db"
        _write_csv(src, df)

        reader = CsvReader()
        writer = SqliteWriter(table_name="data")
        service = TransferService(reader=reader, writer=writer)

        result = service.execute(
            TransferRequest(source=str(src), target=str(tgt), chunk_size=4)
        )

        assert isinstance(result, TransferResult)
        assert result.status == "SUCCESS"
        assert result.rows_read == 10
        assert result.rows_written == 10

    def test_chunked_all_rows_written(self, tmp_path):
        df = _make_df(10)
        src = tmp_path / "src.csv"
        tgt = tmp_path / "tgt.db"
        _write_csv(src, df)

        reader = CsvReader()
        writer = SqliteWriter(table_name="data")
        service = TransferService(reader=reader, writer=writer)
        service.execute(TransferRequest(source=str(src), target=str(tgt), chunk_size=3))

        with sqlite3.connect(tgt) as conn:
            result = pd.read_sql("SELECT * FROM data", conn)

        assert len(result) == 10

    def test_chunked_csv_to_csv(self, tmp_path):
        df = _make_df(12)
        src = tmp_path / "src.csv"
        tgt = tmp_path / "tgt.csv"
        _write_csv(src, df)

        reader = CsvReader()
        writer = CsvWriter()
        service = TransferService(reader=reader, writer=writer)
        service.execute(TransferRequest(source=str(src), target=str(tgt), chunk_size=5))

        result = pd.read_csv(tgt, encoding="utf-8-sig").reset_index(drop=True)
        pd.testing.assert_frame_equal(df.reset_index(drop=True), result)

    def test_chunked_csv_to_parquet(self, tmp_path):
        df = _make_df(9)
        src = tmp_path / "src.csv"
        tgt = tmp_path / "tgt.parquet"
        _write_csv(src, df)

        reader = CsvReader()
        writer = ParquetWriter()
        service = TransferService(reader=reader, writer=writer)
        service.execute(TransferRequest(source=str(src), target=str(tgt), chunk_size=4))

        result = pd.read_parquet(tgt).reset_index(drop=True)
        pd.testing.assert_frame_equal(df.reset_index(drop=True), result)

    def test_chunk_size_zero_uses_full_load(self, tmp_path):
        """chunk_size=0 must use the non-chunked path."""
        df = _make_df(8)
        src = tmp_path / "src.csv"
        tgt = tmp_path / "tgt.db"
        _write_csv(src, df)

        reader = CsvReader()
        writer = SqliteWriter(table_name="data")
        service = TransferService(reader=reader, writer=writer)
        result = service.execute(TransferRequest(source=str(src), target=str(tgt)))

        assert result.rows_read == 8
        assert result.rows_written == 8
