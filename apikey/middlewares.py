from typing import Any
from django.http import HttpRequest, HttpResponseNotAllowed
from .services import apikeyService

class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request:HttpRequest, *args: Any, **kwds: Any) -> Any:
        key = request.headers.get('X-Manager-key', None)
        if apikeyService().check_access(key):
            return self.get_response(request, *args, **kwds)
        return HttpResponseNotAllowed()