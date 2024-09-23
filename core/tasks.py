from celery import shared_task
from repo import models
from django.db.models import Subquery, Count
from uuid import uuid4
from core.services import SubscriptionService, NodeService
from asgiref.sync import sync_to_async, async_to_sync
import asyncio

@shared_task
def check_subscription_aligns(subid):
    return async_to_sync(acheck_subscription_aligns)(subid)

async def acheck_subscription_aligns(subid):
    if not isinstance(subid, models.subscribe):
        try:
            sub = await models.subscribe.objects.aget(id=subid)
        except models.subscribe.DoesNotExist:
            return
    else:
        sub = subid
    asignq = models.assign.objects.filter(subscribe=sub, enable=True, node__enable=True)
    count = await asignq.acount()
    nodeq = models.node.objects.filter()
    nodeCount = await nodeq.acount()
    while count > sub.node_number:
        deleting = await asignq.afirst()
        await deleting.adelete()
        count -= 1
    if count < sub.node_number and count < nodeCount:
        availableNodes = models.node.objects.filter(
            enable=True
        ).exclude(
            id__in=Subquery(
                asignq.values('id')
            )
        ).annotate(
            assign_count=Count('assign')
        ).order_by(
            '-assign_count'
        )
        availableNodesIter = availableNodes.__aiter__()
        while count < sub.node_number and count < nodeCount:
            node = await anext(availableNodesIter)
            uuid = None
            while not uuid:
                _uuid = uuid4()
                if not await models.assign.objects.filter(uuid=_uuid).aexists():
                    uuid = _uuid
            assign = await models.assign.objects.acreate(
                subscribe=sub,
                node=node,
                uuid=uuid
            )
            check_assign_backend.delay(assign.id)
            count += 1

@shared_task
def check_assign_backend(assignid):
    return async_to_sync(acheck_assign_backend)(assignid)

async def acheck_assign_backend(assignid):
    if not isinstance(assignid, models.assign):
        try:
            assign = await models.assign.objects.aget(id=assignid, enable=True)
        except models.assign.DoesNotExist:
            return
    else:
        assign = assignid
    node = await sync_to_async(getattr)(assign, "node")
    service = NodeService(node)
    if not await service.aassignExists(assign.uuid):
        await service.acreateAssign(assign.uuid)

@shared_task
def check_backend_assign(nodeId):
    return async_to_sync(acheck_backend_assign)()

async def acheck_backend_assign(nodeId):
    if not isinstance(nodeId, models.node):
        try:
            node = await models.node.objects.aget(id=nodeId)
        except models.node.DoesNotExist:
            return
    else:
        node = nodeId
    service = NodeService(node)
    backend_assigns = await service.agetAssignAll()
    for i in backend_assigns:
        if not await models.assign.objects.filter(uuid=i, enable=True).aexists():
            await service.adeleteAssign(i)

@shared_task
def check_all_assigns():
    return async_to_sync(acheck_all_assigns)()

async def acheck_all_assigns():
    tasks = []
    async for assign in models.assign.objects.filter(enable=True).aiterator():
        tasks.append(acheck_assign_backend(assign))
        if len(tasks) > 3 :
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)

@shared_task
def check_all_nodes():
    return async_to_sync(acheck_all_nodes)()

async def acheck_all_nodes():
    tasks = []
    async for node in models.node.objects.filter(enable=True).aiterator():
        tasks.append(acheck_backend_assign(node))
        if len(tasks) > 3 :
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)

@shared_task
def check_all_subscriptions():
    return async_to_sync(acheck_all_subscriptions)()

async def acheck_all_subscriptions():
    tasks = []
    async for sub in models.subscribe.objects.all().aiterator():
        tasks.append(acheck_subscription_aligns(sub))
        if len(tasks) > 3 :
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)
