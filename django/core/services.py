from repo import models
from .backends import getBackend
from .models import AssignReport
from traffic import traffic
from .backends.base import baseNodeBackend
from asgiref.sync import sync_to_async
class NodeService:
    def __init__(self, node:models.node):
        self.dbObj = node
        self.backend:baseNodeBackend = getBackend(node.backend)(
            self.dbObj.address,
            self.dbObj.host,
            self.dbObj.auth,
            self.dbObj.settings
        )
    async def agetReportByAssign(self, assign) -> AssignReport:
        return await self.backend.agetReportByAssign(assign)
    async def agetUrlByAssign(self, assign:str, **wargs):
        return await self.backend.agetURL(assign, **wargs)
    async def aassignExists(self, assign:str)->bool:
        assigns = await self.backend.agetAllAssigns()
        return assign in assigns
    async def agetAssignAll(self)->list[str]:
        return await self.backend.agetAllAssigns()
    async def acreateAssign(self, assign:str):
        return await self.backend.aaddSubscription(assign)
    async def adeleteAssign(self, uuid):
        return await self.backend.adeleteSubscription(uuid)

class SubscriptionService:
    def __init__(self, sub:models.subscribe):
        self.dbObj = sub
    async def get_used_traffic(self):
        assigns = models.assign.objects.filter(subscribe=self.dbObj)
        traffics = traffic(0)
        async for i in assigns.aiterator():
            rep = await NodeService(
                    await sync_to_async(getattr)(i,'node')
                ).agetReportByAssign(i)
            traffics += rep.Traffic
        return traffics