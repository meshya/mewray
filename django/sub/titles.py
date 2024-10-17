from repo import models
from asgiref.sync import async_to_sync, sync_to_async
from datetime import datetime

class NormalTitle:
    def __init__(self, subscribe:models.subscribe):
        self.sub = subscribe
    async def normal(self):
        agetattr = sync_to_async(getattr)
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
        name = await agetattr(self.sub, 'api_pk')
        title = f'{name}{progress}'
        return title