"""跳转类型枚举，对应 C# JmpType."""

from enum import IntEnum


class JmpType(IntEnum):
    IfFalse = 0
    IfTrue = 1
    Goto = 2
    ForNext = 3
    DoLoop = 4
    ChooseCase = 5
    TryCatch = 6
