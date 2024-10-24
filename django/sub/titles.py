from repo import models
from asgiref.sync import sync_to_async
from datetime import datetime
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
        ratio = min(spent/full, 1)
        freeSpace = ' '*int((1-ratio)*10)
        fullSpace = '='*int(ratio*10)
        progress = f'[{fullSpace}{freeSpace}]'
        return progress

    async def trafficProgress(self):
        service = SubscriptionService(self.sub)
        usedTraffic = await service.get_used_traffic()
        allowedTraffic = await agetattr(self.sub, 'traffic')
        ratio = allowedTraffic / usedTraffic
        freeSpace = ' '*int((1-ratio)*10)
        fullSpace = '-'*int(ratio*10)
        progress = f'<{fullSpace}{freeSpace}>'
        return progress

    async def normal(self):
        name = await agetattr(self.sub, 'api_pk')
        timeProgress = await self.timeProgress()
        trafficProgress = await self.trafficProgress()
        title = f'{name}{trafficProgress}{timeProgress}'
        return title