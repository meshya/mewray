from repo import models
from .backends import getBackend, AssignNotSynced
from .backends.base import baseNodeBackend
from utils.cache import Cache
from utils.sync import run_multiple_task
from asgiref.sync import async_to_sync
from traffic import traffic

class NodeService:
    def __init__(self, node:models.node):
        self.dbObj = node
        self.backend:baseNodeBackend = getBackend(node.backend)(
            self.dbObj
        )
    def removeuuid(self, uuid):
        return async_to_sync(self.aremoveuuid)(uuid)
    async def aadd(self, assign):
        return await self.backend.aadd(assign.uuid)
    async def aremove(self, assign):
        return await self.backend.aremove(assign.uuid)
    async def aremoveuuid(self, uuid):
        return await self.backend.aremove(uuid)
    async def aexists(self, assign):
        return await self.backend.aexists(assign.uuid)
    async def aisEnable(self, assign):
        return await self.backend.aisEnable(assign.uuid)
    async def aenable(self, assign):
        return await self.backend.aenable(assign.uuid)
    async def adisable(self, assign):
        return await self.backend.adisable(assign.uuid)
    async def atraffic(self, assign, tries=3):
        try:
            return await self.backend.atraffic(assign.uuid)
        except ConnectionError as e:
            if tries:
                return await self.atraffic(assign.uuid, tries=tries-1)
            raise e
    async def atrafficall(self):
        assignq = models.assign.objects.filter(node=self.dbObj)
        alltraffic = traffic(0)
        async for assign in assignq:
            try:
                traf = await self.atraffic(assign)
            except AssignNotSynced:
                traf = traffic(0)
            alltraffic += traf
        return alltraffic
    async def aconfig(self, assign):
        return await self.backend.aconfig(assign.uuid)
    async def aall(self):
        return await self.backend.aall()

class SubscriptionService:
    def __init__(self, sub:models.subscribe):
        self.dbObj = sub
        self.cacheId = sub.id
    @Cache('sub_{cacheId}_traffic', 30)
    async def atraffic(self):
        traffics = []
        tasks = []
        assigns = models.assign.objects.filter(subscribe=self.dbObj)
        async def getTraffic(assign:models.assign):
            node = await assign.aget('node')
            nodeService = NodeService(node)
            try:
                traf = await nodeService.atraffic(assign)
            except AssignNotSynced:
                traf = traffic(0)
            traffics.append(traf)
        async for assign in assigns:
            tasks.append(getTraffic(assign))
        await run_multiple_task(tasks, 1)
        trafficSum = traffic(0)
        for t in traffics: trafficSum+=t
        return trafficSum
