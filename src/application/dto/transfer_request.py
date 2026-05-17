from dataclasses import dataclass


@dataclass
class TransferRequest:
    source: str
    target: str
    source_sep_file: str = ','
    target_sep_file: str = ','
    source_encoding: str = 'utf-8-sig'
    target_encoding: str = 'utf-8-sig'
    custom_query: str = ''

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source cannot be empty")
        if not self.target.strip():
            raise ValueError("target cannot be empty")
