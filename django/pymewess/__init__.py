
from typing import Any

class BaseProtocol:
    all = []
    def __init__ (self): ...
    def __init_subclass__(cls) -> None:
        BaseProtocol.all.append(cls)
    @classmethod
    def get (cls, pname):
        return filter(lambda x: x.__name__ == pname, BaseProtocol.all).__iter__().__next__()
    def url(self, config: "Config"):
        raise

class Config:
    protocol: BaseProtocol
    _attrs = [
        "protocol",
        "address",
        "connection",
        "encrypt",
        "name",
        "id",
        'fingerprint',
        "security",
        "sni",
        "sslpubkey",
        "shortid",
        'serviceName',
        'authority'
    ]
    __spec__ = [
        *_attrs
    ]
    def __init__ ( self,
            protocol="",
            address="",
            connection="",
            encrypt="",
            name="",
            id="",
            fingerprint="",
            security="",
            sni="",
            sslpubkey="",
            shortid="",
            serviceName='',
            authority='',
            spx=''
    ):
        self._set(
            protocol=protocol,
            address=address,
            connection=connection,
            encrypt=encrypt,
            name=name,
            id=id,
            fingerprint=fingerprint,
            security=security,
            sni=sni,
            sslpubkey=sslpubkey,
            shortid=shortid,
            serviceName=serviceName,
            authority=authority,
            spx=spx
        )
    def url(self):
        url = self.protocol.url(self)
        return url
    def _set(self,
            protocol="",
            address="",
            connection="",
            encrypt="",
            name="",
            id="",
            fingerprint="",
            security="",
            sni="",
            sslpubkey="",
            shortid="",
            serviceName="",
            authority='',
            spx=''
            ):
        
        if protocol:
            if isinstance(protocol, str):
                protocol = BaseProtocol.get(protocol)()
            if not isinstance(protocol, BaseProtocol):
                raise Exception(f"protocol {protocol} can not be {type(protocol)}")
        self.protocol = protocol or getattr(self, "protocol", '')        
        self.address = address or getattr(self, "address", '')        
        self.connection = connection or getattr(self, "connection", '')        
        self.encrypt = encrypt or getattr(self, "encrypt", '')        
        self.name = name or getattr(self, "name", '')        
        self.id = id or getattr(self, "id", '')        
        self.fingerprint = fingerprint or getattr(self, "fingerprint", '')        
        self.security = security or getattr(self, "security", '')        
        self.sni = sni or getattr(self, "sni", '')        
        self.sslpubkey = sslpubkey or getattr(self, "sslpubkey", '')        
        self.shortid = shortid or getattr(self, "shortid", '')
        self.serviceName = serviceName or getattr(self, "serviceName", '')
        self.authority = authority or getattr(self, "authority", '')
        self.spx = spx or getattr(self, "spx", '')


class vless(BaseProtocol):
    def url(self, config: Config):
        base = 'vless://'
        '''
        vless://6ab10000-c007-4ba9-a005-d0000000000c@1.2.3:443?type=grpc&serviceName=&authority=&security=reality&pbk=s0a00s9IP-Rf9M00Q-zJpGgS40000000TjsbFWQ&fp=firefox&sni=000.com&sid=d0000006&spx=%0F#Test
        '''
        base += f"{config.id}@{config.address}"
        base += f"?type={config.connection}&serviceName={config.serviceName}&authority={config.authority}"
        base += f"&security={config.security}&pbk={config.sslpubkey}&fp={config.fingerprint}&sni={config.sni}&sid={config.shortid}&spx={config.spx}"
        base += f"#{config.name}"
        return base

class EmptyConfig(Config):
    def __init__(self, name=''):
        super().__init__(protocol='vless', address='xxx.xxx', connection='tcp', name=name, id='xxx')