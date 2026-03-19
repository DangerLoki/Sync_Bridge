from src.application.dto.transfer_request import TransferRequest
from src.domain.models.transfer_result import TransferResult
from src.domain.ports.data_reader import DataReader
from src.domain.ports.data_writer import DataWriter


class TransferService:
    def __init__(self, reader: DataReader, writer: DataWriter) -> None:
        self.reader = reader
        self.writer = writer

    def execute(self, request: TransferRequest) -> TransferResult:
        data = self.reader.read(request.source, sep_file=request.sep_file)
        rows_read = len(data)
        rows_written = self.writer.write(data, request.target, sep_file=request.sep_file)

        return TransferResult(
            source=request.source,
            target=request.target,
            rows_read=rows_read,
            rows_written=rows_written,
            status="SUCCESS",
        )