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

    def execute(self, request: TransferRequest, progress_callback=None) -> TransferResult:
        if request.chunk_size > 0:
            return self._execute_chunked(request, progress_callback=progress_callback)
        return self._execute_full(request, progress_callback=progress_callback)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_full(self, request: TransferRequest, progress_callback=None) -> TransferResult:
        """Load the entire source into memory, then write it at once."""
        logger.debug("Reading from '%s'", request.source)
        data = self.reader.read(
            request.source,
            sep_file=request.source_sep_file,
            custom_query=request.custom_query,
        )
        rows_read = len(data)
        logger.debug("Read %d rows from '%s'", rows_read, request.source)

        logger.debug("Writing to '%s'", request.target)
        rows_written = self.writer.write(
            data,
            request.target,
            sep_file=request.target_sep_file,
            append=False,
        )
        logger.debug("Wrote %d rows to '%s'", rows_written, request.target)
        self.writer.close()

        if progress_callback:
            progress_callback(rows_read=rows_read, 
                              rows_written=rows_written, 
                              chunk_index=0, 
                              done=True)

        return TransferResult(
            source=request.source,
            target=request.target,
            rows_read=rows_read,
            rows_written=rows_written,
            status="SUCCESS",
        )

    def _execute_chunked(self, request: TransferRequest, progress_callback=None) -> TransferResult:
        """Stream the source in chunks of *request.chunk_size* rows."""
        logger.debug(
            "Starting chunked transfer from '%s' (chunk_size=%d)",
            request.source,
            request.chunk_size,
        )
        rows_read = 0
        rows_written = 0

        try:
            for chunk_index, chunk in enumerate(
                self.reader.read_chunks(
                    request.source,
                    chunk_size=request.chunk_size,
                    sep_file=request.source_sep_file,
                    custom_query=request.custom_query,
                )
            ):
                rows_read += len(chunk)
                logger.debug(
                    "Chunk %d: %d rows read (total so far: %d)",
                    chunk_index,
                    len(chunk),
                    rows_read,
                )
                written = self.writer.write(
                    chunk,
                    request.target,
                    sep_file=request.target_sep_file,
                    append=(chunk_index > 0),
                )
                rows_written += written
                logger.debug(
                    "Chunk %d: %d rows written (total so far: %d)",
                    chunk_index,
                    written,
                    rows_written,
                )
                if progress_callback:
                    progress_callback(rows_read=rows_read,
                                      rows_written=rows_written,
                                      chunk_index=chunk_index, 
                                      done=False)
        finally:
            self.writer.close()

        logger.debug(
            "Chunked transfer complete: %d rows read, %d rows written",
            rows_read,
            rows_written,
        )

        return TransferResult(
            source=request.source,
            target=request.target,
            rows_read=rows_read,
            rows_written=rows_written,
            status="SUCCESS",
        )