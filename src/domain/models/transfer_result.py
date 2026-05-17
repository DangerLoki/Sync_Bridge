from dataclasses import dataclass


@dataclass(repr=False)
class TransferResult:
    source: str
    target: str
    rows_read: int
    rows_written: int
    status: str

    def __repr__(self) -> str:
        return (
            f"TransferResult("
            f"source='{self.source}', "
            f"target='{self.target}', "
            f"rows_read={self.rows_read}, "
            f"rows_written={self.rows_written}, "
            f"status='{self.status}')"
        )

    def __str__(self) -> str:
        return (
            f"Status: {self.status} | "
            f"Source: {self.source} | "
            f"Target: {self.target} | "
            f"Rows read: {self.rows_read} | "
            f"Rows written: {self.rows_written}"
        )
