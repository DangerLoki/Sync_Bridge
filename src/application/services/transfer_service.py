import logging

from src.application.dto.transfer_request import TransferRequest
from src.domain.models.transfer_result import TransferResult
from src.domain.ports.data_reader import DataReader
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class TransferService:
    def __init__(self, reader: DataReader, writer: DataWriter) -> None:
        self.reader = reader
        self.writer = writer

    def execute(self, request: TransferRequest) -> TransferResult:
        logger.debug("Reading from '%s'", request.source)
        data = self.reader.read(request.source, sep_file=request.sep_file)
        rows_read = len(data)
        logger.debug("Read %d rows from '%s'", rows_read, request.source)

        logger.debug("Writing to '%s'", request.target)
        rows_written = self.writer.write(data, request.target, sep_file=request.sep_file)
        logger.debug("Wrote %d rows to '%s'", rows_written, request.target)

        return TransferResult(
            source=request.source,
            target=request.target,
            rows_read=rows_read,
            rows_written=rows_written,
            status="SUCCESS",
        )