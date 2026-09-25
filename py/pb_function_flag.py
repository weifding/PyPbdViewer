"""函数标志位，对应 C# PbFunctionFlag."""


class PbFunctionFlag:
    IsPrivate = 0x01
    IsPublic = 0x02
    IsProtected = 0x04
    IsGlobal = 0x08
    IsEvent = 0x10
    IsLocal = 0x20

    @staticmethod
    def has_flag(flag: int, mask: int) -> bool:
        return (flag & mask) != 0
