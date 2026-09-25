"""变量标志位，对应 C# PbVariableFlag."""


class PbVariableFlag:
    IsPrivate = 0x01
    IsProtected = 0x02
    IsShared = 0x04
    IsConstant = 0x08
    IsArray = 0x10
    IsCustom = 0x20
    Invalid = 0x80

    @staticmethod
    def has_flag(flag: int, mask: int) -> bool:
        return (flag & mask) == mask
