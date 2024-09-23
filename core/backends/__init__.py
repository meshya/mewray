from .base import baseNodeBackend
from .xui_backend import XUIBackend
def getBackend(name:str)->baseNodeBackend:
    if name == "XUI":
        return XUIBackend