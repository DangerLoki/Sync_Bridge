class TransferRequest:
    def __init__(self, source: str, target: str, sep_file: str = ',') -> None:
        self.source = source
        self.target = target
        self.sep_file = sep_file