from .base import baseNodeBackend, AssignNotSynced
from django.core.cache import cache
from hashlib import sha256
import aiohttp
import re
from asgiref.sync import sync_to_async as s2a
from traffic import traffic
import pymewess
import json
import ssl
import urllib.parse as urlParse
from repo import models
from utils.cache import Cache
from django.conf import settings

if settings.DEBUG:
    proxy = "http://127.0.0.1:8080"
else:
    proxy = None
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
request_arguments={
    'proxy': proxy,   
    'ssl': ssl_context
}

class ConnectionError(Exception): ...

def email(uuid):
    return f"mewray-{uuid}"

class api:
    def __init__(self, cacheId, auth, address, inboundId):
        self.cacheId = cacheId
        self.auth = auth
        self.address = address
        self.Id = inboundId
        self.headers = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }
        hostregex = r"(https?)://(.+)/?.*"
        hostmatch = re.findall(hostregex, self.address)
        self.protocol, self.host = hostmatch[0]
    async def getLoginCookies(self):
        username = self.auth['username']
        password = self.auth['password']
        cookies = None
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.address}", headers=self.headers, **request_arguments) as resp:
                if resp.status.__str__()[0] != "2":
                    raise ConnectionError()
            data = {"username":username, "password":password}
            _headers = {
                **self.headers,
            }
            async with session.post(f"{self.address}/login", headers=_headers, data=data, **request_arguments) as resp:
                if resp.status.__str__()[0] != "2":
                    raise ConnectionError()
                cookies = dict(resp.cookies)
        return cookies
    async def getSession(self)->aiohttp.ClientSession:
        cookie_cache_key = f"xui_{self.cacheId}_login_cookies"
        cookies = await cache.aget(cookie_cache_key)
        if not cookies:
            cookies = await self.getLoginCookies()
            await cache.aset(cookie_cache_key, cookies, 60*60)
        session = aiohttp.ClientSession(cookies=cookies)
        return session
    async def agetReportAll(self):
        cache_key=f'xui_{self.cacheId}_report'
        data = await cache.aget(cache_key, None)
        if data is None:
            obj = await self.aGetInbound()
            data = obj['clientStats']
            await cache.aset(cache_key, data, 5*60)
        return data
    async def _getClientData(self, uuid, enabled=True, tag=''):
            return {
            "id": self.Id,
            "settings": await s2a(json.dumps)( {
                "clients": [
                    {
                        "id": uuid,
                        "flow": "",
                        "email": email(uuid),
                        "limitIp": 0,
                        "totalGB": 0,
                        "expiryTime": 0,
                        "enable": enabled,
                        "tgId": "",
                        "subId": "mewray",
                        "reset": 0
                    }
                ]
            } )
        }

    async def aCreateClient(self, uuid, tag=''):
        import json
        url = f"{self.address}/panel/inbound/addClient"
        data = await self._getClientData(uuid, tag=tag)
        _headers = {
            **self.headers,
            'Referer': f"{self.address}/panel/inbounds",
            "sec-fetch-site": "same-origin",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": 'cors',
            "Origin": f"{self.protocol}://{self.host}",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        async with await self.getSession() as session:
            async with session.post(url, data=data, headers=_headers, **request_arguments) as resp:
                if resp.status.__str__()[0] != "2":
                    raise ConnectionError()
    async def aUpdateClient(self, uuid, enabled=True, tag=''):
        data = await self._getClientData(uuid, enabled=enabled, tag=tag)
        _headers = {
            **self.headers,
            'Referer': f"{self.address}/panel/inbounds",
            "sec-fetch-site": "same-origin",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": 'cors',
            "Origin": f"{self.protocol}://{self.host}",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        url = f"{self.address}/panel/inbound/updateClient/{uuid}"
        async with await self.getSession() as session:
            async with session.post(url, headers=_headers, data=data, **request_arguments) as resp:
                if resp.status.__str__()[0] != "2":
                    raise ConnectionError()
    async def aDeleteClient(self, uuid):    
        url = f"{self.address}/panel/inbound/{self.Id}/delClient/{uuid}"
        _headers = {
            **self.headers,
            'Referer': f"{self.address}/panel/inbounds",
            "sec-fetch-site": "same-origin",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": 'cors',
            "Origin": f"{self.protocol}://{self.host}"
        }
        async with await self.getSession() as session:
            async with session.post(url, headers=_headers, **request_arguments) as resp:
                if resp.status.__str__()[0] != "2":
                    raise ConnectionError()
    @Cache('XUI_{cacheId}_inbound_check', 10)
    async def aGetInbound(self):
        url = f"{self.address}/panel/inbound/list"
        async with await self.getSession() as session:
            async with session.post(url, headers=self.headers, **request_arguments) as resp:
                json = await resp.json()
        inboundfilter = filter(lambda x: x['id'] == self.Id, json['obj'])
        inbound = inboundfilter.__iter__().__next__()
        return inbound
    @Cache('XUI_{cacheId}_inboundlist', 30)
    async def aGetList(self):
        from json import loads
        inbound = await self.aGetInbound()
        settigsDump = inbound['settings']
        settings = await s2a(loads)(settigsDump)
        return settings['clients']

    async def aGetConfig(self):
        ...

class XUIBackend(baseNodeBackend):
    '''
        Cache names:
        XUI_{id}_Report_All
        XUI_{id}_
    '''

    def __init__(self, node):
        super().__init__(node)
        self.auth = json.loads(self.auth)
        self.setting = json.loads(self.setting)
        self._cacheId = None
        self.api = api(self.cacheId, self.auth, self.address, self.setting['id'])

    @property
    def cacheId(self):
        if self._cacheId is None:
            buffer = self.address.__str__() + self.setting.__str__() + self.auth.__str__()
            buffer = bytes(buffer, 'UTF-8')
            self._cacheId = sha256(buffer).hexdigest()
        return self._cacheId
    async def email(self, uuid):
        return email(uuid)
    async def atraffic(self, uuid):
        reps = await self.api.agetReportAll()
        email = await self.email(uuid)
        Filter = filter(lambda x: x['email'] == email ,reps)
        List = list(Filter)
        if not List.__len__():
            raise AssignNotSynced(uuid)
        rep = List[0]
        return traffic(
            rep['up'] + rep['down'], suffix="B"
        )
    async def aexists(self, uuid):
        subs = await self.api.aGetList()
        return uuid in map(lambda x: x['id'], subs)
    async def aadd(self, uuid):
        return await self.api.aCreateClient(uuid)
    async def aremove(self, uuid):
        return await self.api.aDeleteClient(uuid)
    async def aconfig(self, uuid):
        settings = await self._agetSetting()
        config = pymewess.Config(
            address=f"{self.host}:{settings['port']}",
            connection=settings['network'],
            security=settings['security'],
            protocol=settings['protocol'],
            id=uuid,
        )
        if 'realitySettings' in settings:
            config._set(
                sni=settings['realitySettings']['serverNames'][0],
                sslpubkey=settings['realitySettings']['settings']['publicKey'],
                fingerprint=settings['realitySettings']['settings']['fingerprint'],
                shortid=settings['realitySettings']['shortIds'][0]
            )
            if "spiderX" in settings['realitySettings']['settings']:
                config._set(
                    spx=urlParse.quote(settings['realitySettings']['settings']["spiderX"], safe='')
                )
        return config
    @Cache('XUI_{cacheId}_setting', 20*60)
    async def _agetSetting(self):
        inbound = await self.api.aGetInbound()
        cached = await s2a(json.loads)(inbound['streamSettings'])
        cached['protocol'] = inbound['protocol']
        cached['port'] = inbound['port']
        return cached
    async def aenable(self, uuid):
        return await self.api.aUpdateClient(
            uuid,
            enabled=True,
        )
    async def adisable(self, uuid):
        return await self.api.aUpdateClient(
            uuid,
            enabled=False,
        )
    async def aisEnable(self, uuid):
        subs = await self.api.aGetList()
        _setting = filter(lambda x: x['id']==uuid, subs)
        try:
            setting = next(iter(_setting))
        except StopIteration:
            raise AssignNotSynced(uuid)
        return setting['enable']
    async def aall(self):
        List = await self.api.aGetList()
        return list(
            map(
                lambda x:x['id'],
                List
            )
        )