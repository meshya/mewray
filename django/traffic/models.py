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
                amount = traffic._using_suffix(amount, suffix)
            self.bytes = amount
        elif isinstance(amount, str):
            self.bytes = traffic._from_string(amount)
        elif isinstance(amount, traffic):
            self.bytes = amount.bytes
        else:
            raise
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
        size_units = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        _bytes = self.bytes
        while _bytes >= 1024 and i < len(size_units) - 1:
            _bytes /= 1024
            i += 1
        _bytes = str(f"{_bytes:.2f}").replace('0', ' ').strip().replace(' ', '0')
        if _bytes[-1] == '.':
            _bytes = _bytes[:-1]
        return f"{_bytes or '0'}{size_units[i]}"

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
    def __truediv__(self, other):
        return self.bytes / other.bytes