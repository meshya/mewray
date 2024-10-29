from celery import shared_task
from repo import models
from django.db.models import Subquery, Count
from uuid import uuid4
from core.services import SubscriptionService, NodeService
from asgiref.sync import sync_to_async, async_to_sync
from datetime import datetime
from traffic import traffic
from utils.sync import run_multiple_task

async def sync_sub(sub):
    asignq = models.assign.objects.filter(subscribe=sub, enable=True, node__enable=True)
    count = await asignq.acount()
    nodeq = models.node.objects.filter()
    subNodeNumber = await sync_to_async(getattr)(sub,'node_number')
    nodeCount = await nodeq.acount()
    changedNodes = []
    tasks=[]
    while count > subNodeNumber:
        deleting = await asignq.afirst()
        changingNode = await sync_to_async(getattr)(deleting, 'node')
        if changingNode not in changedNodes:
            changedNodes.append(changingNode)
        deleting.enable = False
        await deleting.asave()
        count -= 1
    if count < subNodeNumber and count < nodeCount:
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
        while count < subNodeNumber and count < nodeCount:
            node = await anext(availableNodesIter)
            uuid = None
            while not uuid:
                _uuid = str(uuid4())
                if not await models.assign.objects.filter(uuid=_uuid).aexists():
                    uuid = _uuid
            assign = await models.assign.objects.acreate(
                subscribe=sub,
                node=node,
                uuid=uuid
            )
            task = sync_to_async(check_assign_backend.delay)(assign.id)
            tasks.append(task)
            count += 1
        for changedNode in changedNodes:
            nodeId = await sync_to_async(getattr)(changedNode, 'id')
            task = sync_to_async(check_backend_assign.delay)(nodeId)
            tasks.append(task)
    await run_multiple_task(tasks, 100)

async def sync_node(node):
    assignq = models.assign.objects.filter(node=node)
    service = NodeService(node)
    tasks = []
    async def a2n(assign):
        await sync_assign(assign, node=node)
    async def n2a(uuid):
        if not await models.assign.objects.filter(uuid=uuid).aexists():
            await service.aremoveuuid(uuid)
    async for assign in assignq:
        tasks.append(a2n(assign))
    for uuid in await service.aall():
        tasks.append(n2a(uuid))
    await run_multiple_task(tasks, 10)

async def sync_assign(assign, node=None):
    if node is None:
        node = await assign.aget('node')
    service = NodeService(node)
    if not await service.aexists(assign):
        await service.aadd(assign)
        return
    localEnable = assign.enable
    nodeEnable = await service.aisEnable(assign)
    if localEnable != nodeEnable:
        if localEnable:
            await service.aenable(assign)
        else:
            await service.adisable(assign)

async def check_sub(sub):
    service = SubscriptionService(sub)
    newEnable = enable = await sync_to_async(getattr)(sub, 'enable')
    usedTraffic = None
    error = None
    usedTraffic = await service.atraffic()
    subTraffic = await sync_to_async(getattr)(sub, 'traffic')
    now = datetime.now()
    newStartDate = startDate = await sync_to_async(getattr)(sub, 'start_date')
    period = await sync_to_async(getattr)(sub, 'period')
    assignq = models.assign.objects.filter(subscribe=sub)
    end = datetime(
        day=startDate.day,
        month=startDate.month,
        year=startDate.year
    ) + period
    if now > end:
        newStartDate = now
        newEnable = True
        usedTraffic = traffic(0)
        await assignq.adelete()
    if enable:
        if usedTraffic > subTraffic:
            newEnable = False
    if enable != newEnable or newStartDate != startDate:
        sub.enable = newEnable
        sub.start_date = newStartDate
        await sub.asave()

@shared_task
def sync_subs_task():
    tasks = []
    for sub in models.subscribe.objects.all():
        tasks.append(sync_sub(sub))
    async_to_sync(run_multiple_task)(tasks, 100)

@shared_task
def sync_sub_task(subId):
    sub = models.subscribe.objects.get(id=subId)
    async_to_sync(sync_sub)(sub)


@shared_task
def sync_nodes_task():
    tasks = []
    for node in models.node.objects.all():
        tasks.append(sync_node(node))
    async_to_sync(run_multiple_task)(tasks, 100)

@shared_task
def check_subs_task():
    tasks = []
    for sub in models.subscribe.objects.all():
        tasks.append(check_sub(sub))
    async_to_sync(run_multiple_task)(tasks, 100)

@shared_task
def sync_assign_task(assignId):
    assign = models.assign.objects.get(id=assignId)
    task = async_to_sync(sync_assign)
    task(assign)

@shared_task
def remove_client_task(assignId):
    assign = models.assign.objects.get(id=assignId)
    node = assign.node
    service = NodeService(node)
    service.removeuuid(assign.uuid)

# async def acheck_node_traffic(nodeId):
#     if not isinstance(nodeId, models.node):
#         try:
#             node = await models.node.objects.aget(id=nodeId)
#         except models.node.DoesNotExist:
#             return
#     else:
#         node = nodeId
#     nodeTraffic = await sync_to_async(getattr)(node, 'max_traffic')
#     service = NodeService(node)
#     assignq = models.assign.objects.filter(
#         node=node
#     )
#     newEnable = enable = await sync_to_async(getattr)(node, 'enable')
#     if not enable:
#         return
#     now = datetime.now()
#     period = await sync_to_async(getattr)(node, 'period')
#     periodStart = await sync_to_async(getattr)(node, 'period_start')
#     end = datetime(
#         day=periodStart.day,
#         month=periodStart.month,
#         year=periodStart.year
#     ) + period
#     if now > end:
#         await assignq.adelete()
#         node.enable = True
#         await node.asave()
#         return
#     editedNodes = 0
#     usedTrafficSum = traffic(0)
#     async for assign in assignq.aiterator():
#         report = await service.agetReportByAssign(assign)
#         usedTrafficSum = usedTrafficSum + report.traffic
#     newEnable = usedTrafficSum < nodeTraffic
#     if enable != newEnable:
#         node.enable = newEnable
#         await node.asave()
#         await assignq.aupdate(enable=False)
#         editedNodes += 1
#         if not newEnable:
#             await sync_to_async(check_all_subscriptions_assigns.delay)()

# async def acheck_all_subscriptions_time_and_traffic():
#     return await run_multiple_task(
#         [
#             acheck_subscription_time_and_traffic(sub) async for sub in models.subscribe.objects.all().aiterator()
#         ]
#     )

# async def acheck_all_assigns():
#     return await run_multiple_task(
#         [
#             acheck_assign_backend(assign) async for assign in models.assign.objects.filter().aiterator()
#         ]
#     )

# async def acheck_all_subscriptions_assigns():
#         return await run_multiple_task(
#             [
#                 acheck_subscription_assigns(sub) async for sub in models.subscribe.objects.all().aiterator()
#             ]
#         )

# async def acheck_all_nodes_traffic():
#     return await run_multiple_task(
#         [
#             acheck_node_traffic(node) async for node in models.node.objects.all().aiterator()
#         ]
#     )

# async def acheck_all_nodes():
#         return await run_multiple_task(
#             [
#                 acheck_backend_assign(node) async for node in models.node.objects.filter(enable=True).aiterator()
#             ]
#         )


# @shared_task
# def check_all_assigns():
#     return async_to_sync(acheck_all_assigns)()

# @shared_task
# def check_all_nodes():
#     return async_to_sync(acheck_all_nodes)()

# @shared_task
# def check_all_nodes_traffic():
#     return async_to_sync(acheck_all_nodes_traffic)()

# @shared_task
# def check_all_subscriptions_assigns():
#     return async_to_sync(acheck_all_subscriptions_assigns)()

# @shared_task
# def check_all_subscriptions_time_and_traffic():
#     return async_to_sync(acheck_all_subscriptions_time_and_traffic)()

# @shared_task
# def check_backend_assign(nodeId):
#     return async_to_sync(acheck_backend_assign)(nodeId)

# @shared_task
# def check_assign_backend(assignid):
#     return async_to_sync(acheck_assign_backend)(assignid)

# @shared_task
# def check_subscription_assigns(subid):
#     return async_to_sync(acheck_subscription_assigns)(subid)
