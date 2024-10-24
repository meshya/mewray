from typing import Any
from .base import baseNodeBackend, AssignNotSynced
from core.models import AssignReport
from django.core.cache import cache
from hashlib import sha256
import aiohttp
import re
from core.models import AssignReport
from asgiref.sync import sync_to_async as s2a
from traffic import traffic
import pymewess
import json
import ssl
import urllib.parse as urlParse

proxy = "http://127.0.0.1:8080"
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
request_arguments={
#    'proxy': proxy,   
    'ssl': ssl_context
}


class ConnectionError(Exception): ...

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
    async def aCreateClient(self, uuid):
        import json
        url = f"{self.address}/panel/inbound/addClient"
        data = {
            "id": self.Id,
            "settings": json.dumps( {
                "clients": [
                    {
                        "id": uuid,
                        "flow": "",
                        "email": f"mewray{sha256(bytes(uuid, 'UTF-8')).hexdigest()}",
                        "limitIp": 0,
                        "totalGB": 0,
                        "expiryTime": 0,
                        "enable": True,
                        "tgId": "",
                        "subId": "mewray",
                        "reset": 0
                    }
                ]
            } )
        }
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
    async def aGetInbound(self):
        cacheKey = f"XUI_{self.cacheId}_inbound_check"
        cached = await cache.aget(cacheKey)
        if cached :
            return cached
        url = f"{self.address}/panel/inbound/list"
        async with await self.getSession() as session:
            async with session.post(url, headers=self.headers, **request_arguments) as resp:
                json = await resp.json()
                inboundfilter = filter(lambda x: x['id'] == self.Id, json['obj'])
                inbound = inboundfilter.__iter__().__next__()
                await cache.aset(cacheKey, inbound, 10)
                return inbound
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

    def __init__(self, address, host, auth, settings):
        auth = json.loads(auth)
        settings = json.loads(settings)
        super().__init__(address, host, auth, settings)
        self._cacheId = None
        self.api = api(self.cacheId, auth, address, settings['id'])

    @property
    def cacheId(self):
        if self._cacheId is None:
            buffer = self.address.__str__() + self.setting.__str__() + self.auth.__str__()
            buffer = bytes(buffer, 'UTF-8')
            self._cacheId = sha256(buffer).hexdigest()
        return self._cacheId

    def email(self, uuid):
        return f"mewray{sha256(bytes(uuid, 'UTF-8')).hexdigest()}"

    async def agetReportByAssign(self, uuid) -> AssignReport:
        reps = await self.api.agetReportAll()
        email = self.email(uuid)
        Filter = filter(lambda x: x['email'] == email ,reps)
        List = list(Filter)
        if not List.__len__():
            raise AssignNotSynced(uuid)
        rep = List[0]
        return self._convertReport(rep)

    def _convertReport(self, rep)->AssignReport:
        report = AssignReport()
        report.Connections = 0
        report.Traffic = traffic(
            rep['up'] + rep['down'], suffix="B"
        )
        return report


    async def agetAllReport(self):
        reports = await self.api.agetReportAll()
        return list(
            map(
                self._convertReport,
                reports
            )
        )
    async def agetAllAssigns(self):
        cacheId = f'XUI_{self.cacheId}_AllAssigns'
        cached = await cache.aget(cacheId)
        if cached:
            return cached
        subs = await self.api.aGetList()
        cached = list(
            map(
                lambda x: x['id'],
                subs
            )
        )
        await cache.aset(cacheId, cached, 60)
        return cached
    async def aaddSubscription(self, uuid):
        return await self.api.aCreateClient(uuid)
    async def adeleteSubscription(self, uuid):
        return await self.api.aDeleteClient(uuid)
    async def agetURL(self, uuid, name=""):
        settings = await self._agetSetting()
        config = pymewess.Config(
            address=f"{self.host}:{settings['port']}",
            connection=settings['network'],
            security=settings['security'],
            protocol=settings['protocol'],
            id=uuid,
            name=name
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
        return config.url()
    async def _agetSetting(self):
        cachekey = f"XUI_{self.cacheId}_setting"
        cached = await cache.aget(cachekey)
        if cached is None:
            inbound = await self.api.aGetInbound()
            cached = await s2a(json.loads)(inbound['streamSettings'])
            cached['protocol'] = inbound['protocol']
            cached['port'] = inbound['port']
            await cache.aset(cachekey, cached, 20*60)
        return cached
