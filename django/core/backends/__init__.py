from .base import baseNodeBackend, AssignNotSynced
from .xui_backend import XUIBackend
def getBackend(name:str)->baseNodeBackend:
    if name == "XUI":
        return XUIBackend