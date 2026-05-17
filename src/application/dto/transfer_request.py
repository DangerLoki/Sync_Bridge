from dataclasses import dataclass, field


@dataclass
class TransferRequest:
    source: str
    target: str
    source_sep_file: str = ','
    target_sep_file: str = ','
    source_encoding: str = 'utf-8-sig'
    target_encoding: str = 'utf-8-sig'
    custom_query: str = ''
    chunk_size: int = 0  # 0 = load all at once; > 0 = stream in chunks of this size

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source cannot be empty")
        if not self.target.strip():
            raise ValueError("target cannot be empty")
        if self.chunk_size < 0:
            raise ValueError("chunk_size must be >= 0")
