class TransferError(Exception):
    """Base exception for transfer-related errors."""


class SourceReadError(TransferError):
    """Raised when the source cannot be read."""


class TargetWriteError(TransferError):
    """Raised when the target cannot be written."""


class InvalidSourceError(TransferError):
    """Raised when the source path, file, or structure is invalid."""


class InvalidTargetError(TransferError):
    """Raised when the target path, file, or structure is invalid."""