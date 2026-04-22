from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    InvalidTargetError,
    SourceReadError,
    TargetWriteError,
    TransferError,
)


class TestTransferExceptions:
    def test_transfer_error_is_exception(self):
        assert issubclass(TransferError, Exception)

    def test_source_read_error_inherits_transfer_error(self):
        assert issubclass(SourceReadError, TransferError)

    def test_target_write_error_inherits_transfer_error(self):
        assert issubclass(TargetWriteError, TransferError)

    def test_invalid_source_error_inherits_transfer_error(self):
        assert issubclass(InvalidSourceError, TransferError)

    def test_invalid_target_error_inherits_transfer_error(self):
        assert issubclass(InvalidTargetError, TransferError)

    def test_source_read_error_can_be_raised_with_message(self):
        with __import__("pytest").raises(SourceReadError, match="something wrong"):
            raise SourceReadError("something wrong")

    def test_target_write_error_can_be_raised_with_message(self):
        with __import__("pytest").raises(TargetWriteError, match="write failed"):
            raise TargetWriteError("write failed")

    def test_invalid_source_error_can_be_raised_with_message(self):
        with __import__("pytest").raises(InvalidSourceError, match="bad source"):
            raise InvalidSourceError("bad source")

    def test_invalid_target_error_can_be_raised_with_message(self):
        with __import__("pytest").raises(InvalidTargetError, match="bad target"):
            raise InvalidTargetError("bad target")

    def test_all_errors_caught_as_transfer_error(self):
        for cls in (SourceReadError, TargetWriteError, InvalidSourceError, InvalidTargetError):
            try:
                raise cls("msg")
            except TransferError:
                pass
            else:
                raise AssertionError(f"{cls} not caught as TransferError")
