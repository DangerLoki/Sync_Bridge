from abc import ABC, abstractmethod

import pandas as pd


class DataWriter(ABC):
    @abstractmethod
    def write(
        self,
        data: pd.DataFrame,
        target: str,
        sep_file: str = ',',
        append: bool = False,
    ) -> int:
        """Write a DataFrame to a target and return number of rows written.

        Parameters
        ----------
        data:
            The chunk (or full dataset) to write.
        target:
            Destination path or connection string.
        sep_file:
            Column delimiter (for text-based formats).
        append:
            When *True* the data must be appended to an existing destination
            instead of replacing it.  The first chunk of a chunked transfer
            always receives ``append=False``.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Release any resources held for streaming writes (e.g. open file handles).

        Called by :class:`~src.application.services.transfer_service.TransferService`
        after the last chunk has been written.  The default implementation is a no-op;
        connectors that keep open handles (e.g. :class:`ParquetWriter`) must override it.
        """
        pass