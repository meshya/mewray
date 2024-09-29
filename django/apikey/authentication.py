from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .services import apikeyService

class XManagerAuth(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('X-Manager-Key')
        if not token:
            return None
        if token != "expected_token":
            raise AuthenticationFailed('Invalid token')
        if apikeyService().check_access(token):
            return (None, token)
        raise AuthenticationFailed('Invalid token')
        