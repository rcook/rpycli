from enum import Enum
from typing import Self


class ArgEnum(Enum):
    @classmethod
    def from_arg(cls, s: str) -> Self:
        for member in cls:
            if member.arg == s:
                return member
        raise ValueError(f"invalid value '{s}'")

    @property
    def arg(self) -> str:
        return self.name.lower()
