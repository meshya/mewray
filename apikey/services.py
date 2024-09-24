from .models import access

class apikeyService:
    def __init__(self):
        ...
    def check_access(self, key):
        try:
            access.objects.get(key=key)
        except access.DoesNotExist:
            return False
        return access.access
