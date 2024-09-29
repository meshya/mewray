from drf_spectacular.extensions import OpenApiAuthenticationExtension

class authentication(OpenApiAuthenticationExtension):
    target_class = 'apikey.authentication.XManagerAuth'  # full import path OR class ref
    name = 'XManagerKey'  # name used in the schema
    priority = 2

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Manager-Key',
        }