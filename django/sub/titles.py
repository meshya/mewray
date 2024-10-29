from repo import models
from asgiref.sync import sync_to_async
from datetime import datetime
from traffic import traffic
from core.services import SubscriptionService
agetattr = sync_to_async(getattr)

class NormalTitle:
    def __init__(self, subscribe:models.subscribe):
        self.sub = subscribe
    async def timeProgress(self):
        startDate = await agetattr(self.sub, 'start_date')
        start = datetime(
            day=startDate.day,
            month=startDate.month,
            year=startDate.year
        )
        now = datetime.now()
        spent = now - start
        full = await agetattr(self.sub, 'period')
        fullAtDays = int(full.total_seconds() / (24 * 3600))
        spentAtDays = int(spent.total_seconds() / (24 * 3600))
        ratio = min(spent/full, 1)
        freeSpace = ' '*int((1-ratio)*10)
        fullSpace = '='*int(ratio*10)
        progress = f'[{fullSpace}{spentAtDays}/{fullAtDays}{freeSpace}]'
        return progress

    async def trafficProgress(self):
        service = SubscriptionService(self.sub)
        usedTraffic = await service.atraffic()
        allowedTraffic = await agetattr(self.sub, 'traffic')
        if not isinstance(allowedTraffic, traffic):
            allowedTraffic = traffic(allowedTraffic, suffix='M')
        ratio = min (usedTraffic / allowedTraffic, 1)
        freeSpace = ' '*int((1-ratio)*16)
        fullSpace = '-'*int((ratio)*16)
        progress = f'<{fullSpace}{str(usedTraffic)}/{str(allowedTraffic)}{freeSpace}>'
        return progress

    async def normal(self):
        name = await agetattr(self.sub, 'api_pk')
        timeProgress = await self.timeProgress()
        trafficProgress = await self.trafficProgress()
        title = f'{name}{trafficProgress}{timeProgress}'
        return title