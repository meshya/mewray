from .middlewares import Middleware
def apikey_protect(view):
    return Middleware(view)