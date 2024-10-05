from rest_framework.authentication import BaseAuthentication
from .services import apikeyService
from .exceptions import NoApiKey, InvalidApiKey

class XManagerAuth(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('X-Manager-Key')
        if not token:
            raise NoApiKey()
        if apikeyService().check_access(token):
            return (None, token)
        raise InvalidApiKey('Invalid token')
        