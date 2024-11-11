from celery import shared_task
from repo import models
from django.db.models import Subquery, Count
from uuid import uuid4
from core.services import SubscriptionService, NodeService
from asgiref.sync import sync_to_async, async_to_sync
from datetime import datetime, date
from traffic import traffic
from utils.sync import run_multiple_task

async def sync_sub(sub):
    if not await sub.aget('enable'):
        return
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
            'assign_count'
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
            task = sync_to_async(sync_assign_task.delay)(assign.id)
            tasks.append(task)
            count += 1
        for changedNode in changedNodes:
            nodeId = await sync_to_async(getattr)(changedNode, 'id')
            task = sync_to_async(sync_nodes_task.delay)(nodeId)
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
    '''
1.Assign exists in node?
=>syncs enable status
1.else?
=>creates assign
    '''
    if node is None:
        node = await assign.aget('node')
    service = NodeService(node)
    if not await service.aexists(assign):
        await service.aadd(assign)
        return
    localEnable = await assign.aget('enable')
    nodeEnable = await service.aisEnable(assign)
    if localEnable != nodeEnable:
        if localEnable:
            await service.aenable(assign)
        else:
            await service.adisable(assign)



async def check_sub(sub):
    '''
1. End duration?
=> Unlink and disable all assigns
=> Resets duration

2. End traffic?
=> Disables subscribe
=> Disables all assigns
    '''
    service = SubscriptionService(sub)
    newEnable = enable = await sync_to_async(getattr)(sub, 'enable')
    usedTraffic = None
    error = None
    usedTraffic = await service.atraffic()
    subTraffic = await sync_to_async(getattr)(sub, 'traffic')
    if not isinstance(subTraffic, traffic):
        subTraffic = traffic(subTraffic, suffix='M')
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
        newStartDate = now.date()
        newEnable = True
        usedTraffic = traffic(0)
        await assignq.aupdate(enable=False, subscribe=None)
    if enable:
        if usedTraffic > subTraffic:
            newEnable = False
            await assignq.aupdate(enable=False)
    if enable != newEnable or newStartDate != startDate:
        sub.enable = newEnable
        sub.start_date = newStartDate
        await sub.asave()

async def check_node(node:models.node):
    '''
1. End duration?
=> Deletes all assigns
=> Resets duration

2. End traffic?
=> Disables node
=> Disables all assigns
    '''
    service = NodeService(node)
    assignq = models.assign.objects.filter(node=node)
    usedTraffic = await service.atrafficall()
    allowedTraffic = await node.aget('max_traffic')
    if not isinstance(allowedTraffic, traffic):
        allowedTraffic = traffic(allowedTraffic, suffix='M')
    duration = await node.aget('period')
    durationStart = newDurationStart = await node.aget('period_start')
    end = datetime(
        day=durationStart.day,
        month=durationStart.month,
        year=durationStart.year
    ) + duration
    now = datetime.now()
    enable = newEnable = await node.aget('enable')
    if now > end:
        newEnable = True
        newDurationStart = now.date()
        usedTraffic = traffic(0)
        await assignq.adelete()
    if enable:
        if usedTraffic > allowedTraffic:
            newEnable = False
            await assignq.aupdate(enable=False)
    if enable != newEnable or newDurationStart != durationStart:
        node.enable = newEnable
        node.period_start = newDurationStart
        await node.asave()


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
def sync_node_task(nodeId):
    node = models.node.objects.get(id=nodeId)
    task = async_to_sync(sync_node)
    task(node)


@shared_task
def check_subs_task():
    tasks = []
    for sub in models.subscribe.objects.all():
        tasks.append(check_sub(sub))
    async_to_sync(run_multiple_task)(tasks, 10)


@shared_task
def check_nodes_task():
    tasks = []
    for node in models.node.objects.all():
        tasks.append(check_node(node))
    async_to_sync(run_multiple_task)(tasks, 10)

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
