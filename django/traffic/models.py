import re
from functools import total_ordering

__all__=[
    'traffic'
]

@total_ordering
class traffic:
    def __init__(self, *args, suffix=None):
        if not args.__len__() or not args[0]:
            self.bytes = 0
            return
        amount = args[0]
        if isinstance(amount, int):
            if suffix:
                amount = traffic._from_suffix(amount, suffix)
            self.bytes = amount
        elif isinstance(amount, str):
            self.bytes = traffic._from_string(amount)
        elif isinstance(amount, traffic):
            self.bytes = amount.bytes
        else:
            raise
    def __new__(cls, *args):
        return super(cls, traffic).__new__(cls)
    @classmethod
    def _from_string(cls, string):
        reg = r"(\d+)[A-z][bB]"
        match = re.match(reg, string)
        if match:
            string = string[:-1]
        assert not re.match(r"(\d+)[A-z]", string)
        suffix = string[-1].upper()
        amount = int(string[:-1])
        return cls._using_suffix(amount, suffix)
    @classmethod
    def _using_suffix(cls, amount, suffix):
        factor = 1
        match suffix:
            case 'B':
                factor = 1
            case 'K':
                factor = 1024
            case 'M':
                factor = 1024 ** 2
            case 'G':
                factor = 1024 ** 3
            case 'T':
                factor = 1024 ** 4
            case _:
                raise
        return factor * amount

    def __str__(self):
        return self.bytes.__str__()
    def __repr__(self) -> str:
        return f'<traffic {self.bytes} bytes>'
    def __add__(self, other):
        if not isinstance(other, type(self)):
            other = type(self)(other)
        return type(self)(self.bytes+other.bytes)
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            other = type(self)(other)
        return self.bytes == other.bytes
    def __gt__(self, other):
        if not isinstance(other, type(self)):
            other = type(self)(other)
        return self.bytes > other.bytes