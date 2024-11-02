from utils.cache import Cache
from datetime import datetime
from repo import models
from django.core.cache import caches
from core import services
from traffic import traffic
from pymewess import EmptyConfig
from core.backends import AssignNotSynced
from django.http import HttpResponse

class BaseDesigner:
    def __init__(self, sub:models.subscribe) -> None:
        self.sub = sub
        self.cacheId = sub.id
    async def design(self)->str:
        raise

class Designer(BaseDesigner):
    @Cache('Designer_{cacheId}_days', 1, cache=caches['mem'])
    async def days(self):
        startDate = await self.sub.aget('start_date')
        start = datetime(
            day=startDate.day,
            month=startDate.month,
            year=startDate.year
        )
        now = datetime.now()
        full = await self.sub.aget('period')
        remains = (start + full) - now
        remainsAtDays = int(remains.total_seconds() / (24 * 3600))
        return remainsAtDays
    
    @Cache('disigner_{cacheId}_trp', 1, cache=caches['mem'])
    async def trafficProgress(self):
        usableTraffic = await self.traffic()
        allowedTraffic = await self.sub.aget('traffic')
        ratio = min (usableTraffic / allowedTraffic, 1)
        freeSpace = ' '*int((1-ratio)*14)
        fullSpace = '-'*int((ratio)*14)
        progress = f'<{fullSpace}{str(usableTraffic)}/{str(allowedTraffic)}{freeSpace}>'
        return progress

    @Cache('designer_{cacheId}_tmp')
    async def timeProgress(self):
        startDate = await self.sub.aget('start_date')
        start = datetime(
            day=startDate.day,
            month=startDate.month,
            year=startDate.year
        )
        now = datetime.now()
        spent = now - start
        full = await self.sub.aget('period')
        fullAtDays = int(full.total_seconds() / (24 * 3600))
        spentAtDays = int(spent.total_seconds() / (24 * 3600))
        ratio = min(spent/full, 1)
        freeSpace = ' '*int((1-ratio)*10)
        fullSpace = '='*int(ratio*10)
        progress = f'[{fullSpace}{spentAtDays}/{fullAtDays}{freeSpace}]'
        return progress

    @Cache('designer_{cacheId}_traffic', 1, cache=caches['mem'])
    async def traffic(self) -> traffic:
        service = services.SubscriptionService(self.sub)
        usedTraffic = await service.atraffic()
        allowedTraffic = await self.sub.aget('traffic')
        if not isinstance(allowedTraffic, traffic):
            allowedTraffic = traffic(allowedTraffic, suffix='M')
        usableTraffic = allowedTraffic - usedTraffic
        return usableTraffic
    
    async def traffic_all(self):
        allowedTraffic = await self.sub.aget('traffic')
        if not isinstance(allowedTraffic, traffic):
            allowedTraffic = traffic(allowedTraffic, suffix='M')
        return allowedTraffic

    @Cache('design_{cacheId}_title', 1, cache=caches['mem'])
    async def title(self):

        name = await self.sub.aget('api_pk')
        timeProgress = await self.timeProgress()
        trafficProgress = await self.trafficProgress()
        title = f'{name}{trafficProgress}{timeProgress}'

        return title


    async def design(self) -> str:
        name = await self.sub.aget('api_pk')
        days = await self.days()
        traf = await self.traffic()
        allt = await self.traffic_all()
        full = await self.sub.aget('period')
        assignsQ = models.assign.objects.filter(subscribe=self.sub)
        resp = ''
        async for i in assignsQ:
            node = await i.aget('node')
            nodeService = services.NodeService(node)
            assignStatus = await nodeService.aexists(i)
            try:
                if assignStatus :
                    title = await self.title()
                    config = await nodeService.aconfig(i)
                else:
                    raise AssignNotSynced(await i.aget('uuid'))
            except AssignNotSynced:
                title = "Creating config, reload this sub 1min later"
                config = EmptyConfig()
            config._set(name=title)
            url = config.url()
            resp += url
        headers = {
            'subscription-userinfo': f'upload=0; download={allt.bytes - traf.bytes}; total={allt.bytes}; expire={days}',
            'profile-update-interval': 5,
            'profile-title': name
        }
        return HttpResponse(resp, headers=headers)

