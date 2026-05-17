import logging
from typing import Any, Literal

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)
ParquetCompression = Literal['snappy', 'gzip', 'brotli', 'lz4', 'zstd', None]


class ParquetWriter(DataWriter):
    """Writes DataFrames to a Parquet file.

    In chunked-transfer mode the writer keeps an open ``pyarrow.parquet.ParquetWriter``
    between successive ``write(..., append=True)`` calls.  The file is finalised and
    closed when :meth:`close` is called by :class:`TransferService` after the last chunk.
    """

    def __init__(
        self,
        compression: ParquetCompression = 'snappy',
        columns: list[str] | None = None,
    ) -> None:
        self.compression = compression
        self.columns = columns
        self._pq_writer: Any = None  # pyarrow.parquet.ParquetWriter | None

    def write(
        self,
        data: pd.DataFrame,
        target: str,
        sep_file: str = ',',
        append: bool = False,
    ) -> int:
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError as exc:
            raise TargetWriteError(
                "Pacote 'pyarrow' não está instalado. Execute: pip install pyarrow"
            ) from exc

        try:
            if self.columns:
                data = data[self.columns]

            table = pa.Table.from_pandas(data, preserve_index=False)

            if not append:
                # First (or only) chunk — close any leftover writer and start fresh.
                self._close_pq_writer()
                self._pq_writer = pq.ParquetWriter(
                    target, table.schema, compression=self.compression
                )
                logger.debug(
                    "Opened ParquetWriter for '%s' (compression=%s)", target, self.compression
                )
            elif self._pq_writer is None:
                # append=True but no open writer — shouldn't happen in normal flow.
                self._pq_writer = pq.ParquetWriter(
                    target, table.schema, compression=self.compression
                )

            logger.debug("Writing %d rows to Parquet file: %s", len(data), target)
            self._pq_writer.write_table(table)
            logger.debug("Parquet row-group written: %s", target)

            return len(data)
        except Exception as exc:
            self._close_pq_writer()
            logger.error("Failed to write Parquet '%s': %s", target, exc)
            raise TargetWriteError(f"Failed to write Parquet target: {target}") from exc

    def close(self) -> None:
        """Finalise and close the underlying Parquet file (called after last chunk)."""
        self._close_pq_writer()

    def __del__(self) -> None:
        """Ensure the Parquet file is finalised even if close() is never called."""
        self._close_pq_writer()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _close_pq_writer(self) -> None:
        if self._pq_writer is not None:
            try:
                self._pq_writer.close()
                logger.debug("ParquetWriter closed.")
            except Exception:
                pass
            self._pq_writer = None
