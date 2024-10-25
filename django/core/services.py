from repo import models
from .backends import getBackend
from .models import AssignReport
from traffic import traffic
from .backends.base import baseNodeBackend
from asgiref.sync import sync_to_async, async_to_sync
from celery import shared_task
from django.core.cache import cache
from traffic import traffic
import time


class NodeService:
    def __init__(self, node:models.node):
        self.dbObj = node
        self.backend:baseNodeBackend = getBackend(node.backend)(
            self.dbObj.address,
            self.dbObj.host,
            self.dbObj.auth,
            self.dbObj.settings
        )
    async def amakeSureExists(self, assign:models.assign):
        state = await self.aassignExists(assign)
        if state:
            return "CREATED"
        task = sync_to_async(_create_assign.delay)
        await task(assign.id)
        return "CREATING"
    async def agetReportByAssign(self, assign) -> AssignReport:
        if isinstance(assign, models.assign):
            uuid = await sync_to_async(lambda: assign.uuid)
        else:
            uuid = assign
        return await self.backend.agetReportByAssign(uuid)
    async def agetUrlByAssign(self, assign:str, **wargs):
        if isinstance(assign, models.assign):
            uuid = await sync_to_async(lambda: assign.uuid)
        else:
            uuid = assign
        return await self.backend.agetURL(uuid, **wargs)
    async def aassignExists(self, assign:models.assign)->bool:
        if isinstance(assign, models.assign):
            uuid = await sync_to_async(lambda: assign.uuid)
        else:
            uuid = assign
        assigns = await self.backend.agetAllAssigns()
        return uuid in assigns
    async def agetAssignAll(self)->list[str]:
        return await self.backend.agetAllAssigns()
    async def acreateAssign(self, assign:models.assign):
        if isinstance(assign, models.assign):
            uuid = await sync_to_async(lambda: assign.uuid)
        else:
            uuid = assign
        return await self.backend.aaddSubscription(uuid)
    async def adeleteAssign(self, assign:models.assign):
        if isinstance(assign, models.assign):
            uuid = await sync_to_async(lambda: assign.uuid)
        else:
            uuid = assign
        return await self.backend.adeleteSubscription(uuid)

class SubscriptionService:
    def __init__(self, sub:models.subscribe):
        self.dbObj = sub
    async def get_used_traffic(self, timeout=None):
        cacheKey = f'subs_{self.dbObj.id}_traffic'
        Traffic = await cache.aget(cacheKey, None)
        if Traffic is None:
            task = await sync_to_async(_get_used_traffic.delay)(self.dbObj.id, cacheKey)
            start_waiting = time.time()
            while timeout is None or time.time() - start_waiting < timeout:
                state = task.state
                if state == "FAILURE":
                    raise RuntimeError()
                if state == "SUCCESS":
                    Traffic = task.result
                    break
            if Traffic is None:
                raise TimeoutError()
        if Traffic is None:
            return traffic(0)
        return Traffic

@shared_task(trail=True)
def _get_used_traffic(subId, cacheKey):
    subq = models.subscribe.objects.filter(id=subId)
    if not subq.exists():
        return None
    sub = subq.first()
    assigns = models.assign.objects.filter(subscribe=sub)
    traffics = traffic(0)
    for i in assigns.iterator():
        node = i.node
        service = NodeService(node)
        rep = async_to_sync(service.agetReportByAssign)(i)
        traffics += rep.Traffic
    cache.set(cacheKey, traffics, 60)
    return traffics

@shared_task(trail=True)
def _create_assign(assignId):
    assign = models.assign.objects.get(id=assignId)
    ns = NodeService(assign.node)
    task = async_to_sync(ns.acreateAssign)
    return task(assign)