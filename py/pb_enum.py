"""PB 枚举，对应 C# PbEnum."""


class PbEnum:
    def __init__(self):
        self.index: int = 0
        self.name: str = ""
        self.items: dict = {}
