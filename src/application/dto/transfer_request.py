class TransferRequest:
    def __init__(self, source: str, target: str, source_sep_file: str = ',', target_sep_file: str = ',') -> None:
        self.source = source
        self.target = target
        self.source_sep_file = source_sep_file
        self.target_sep_file = target_sep_file