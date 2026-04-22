import pytest

from src.domain.models.transfer_result import TransferResult


class TestTransferResult:
    def test_attributes_are_set_correctly(self):
        result = TransferResult(
            source="file.csv",
            target="db.sqlite",
            rows_read=10,
            rows_written=10,
            status="SUCCESS",
        )

        assert result.source == "file.csv"
        assert result.target == "db.sqlite"
        assert result.rows_read == 10
        assert result.rows_written == 10
        assert result.status == "SUCCESS"

    def test_repr_contains_all_fields(self):
        result = TransferResult(
            source="in.csv",
            target="out.db",
            rows_read=5,
            rows_written=5,
            status="SUCCESS",
        )
        r = repr(result)

        assert "in.csv" in r
        assert "out.db" in r
        assert "rows_read=5" in r
        assert "rows_written=5" in r
        assert "SUCCESS" in r

    def test_str_contains_all_fields(self):
        result = TransferResult(
            source="in.csv",
            target="out.db",
            rows_read=3,
            rows_written=3,
            status="SUCCESS",
        )
        s = str(result)

        assert "in.csv" in s
        assert "out.db" in s
        assert "3" in s
        assert "SUCCESS" in s

    def test_zero_rows(self):
        result = TransferResult(
            source="empty.csv",
            target="out.db",
            rows_read=0,
            rows_written=0,
            status="SUCCESS",
        )

        assert result.rows_read == 0
        assert result.rows_written == 0

    def test_failure_status(self):
        result = TransferResult(
            source="src",
            target="tgt",
            rows_read=0,
            rows_written=0,
            status="FAILURE",
        )

        assert result.status == "FAILURE"
