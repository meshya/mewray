from celery import shared_task
from repo import models
from django.db.models import Subquery, Count
from uuid import uuid4
from core.services import SubscriptionService, NodeService
from asgiref.sync import sync_to_async, async_to_sync
from datetime import datetime
from traffic import traffic
import asyncio

async def run_multiple_task(tasks, chunk=1, delay=0):
    runThisTasks = []
    taskIter = iter(tasks)
    allTasksDone = False
    errors = []
    while not allTasksDone:
        try:
            for _ in range(chunk):    
                _task = next(taskIter)
                async def task():
                    try:
                        await _task
                    except Exception as e:
                        errors.append(e)
                runThisTasks.append(task())
        except (StopAsyncIteration, StopIteration):
            allTasksDone = True
        if tasks:
            await asyncio.sleep(delay)
            await asyncio.gather(*runThisTasks)
        runThisTasks = []
    if errors:
        errorStr = '\n,'.join(map(str, errors))
        raise Exception(f"Multiple errors: {errorStr}")


async def acheck_subscription_assigns(subid):
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
    subNodeNumber = await sync_to_async(getattr)(sub,'node_number')
    nodeCount = await nodeq.acount()
    changedNodes = []
    while count > subNodeNumber:
        deleting = await asignq.afirst()
        changingNode = await sync_to_async(getattr)(deleting, 'node')
        if changingNode not in changedNodes:
            changedNodes.append(changingNode)
        await deleting.adelete()
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
            await sync_to_async(check_assign_backend.delay)(assign.id)
            count += 1
        for changedNode in changedNodes:
            nodeId = await sync_to_async(getattr)(changedNode, 'id')
            await sync_to_async(check_backend_assign.delay)(nodeId)

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
    if not await service.aassignExists(assign):
        await service.acreateAssign(assign)

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

async def acheck_subscription_time_and_traffic(subid):
    if not isinstance(subid, models.subscribe):
        try:
            sub = await models.subscribe.objects.aget(id=subid)
        except models.subscribe.DoesNotExist:
            return
    else:
        sub = subid
    service = SubscriptionService(sub)
    newEnable = enable = await sync_to_async(getattr)(sub, 'enable')
    usedTraffic = None
    error = None
    for _ in range(3):
        try:
            usedTraffic = await service.get_used_traffic()
            break
        except RuntimeError as e:
            error = e
            continue
    if usedTraffic is None:
        error = error or RuntimeError(f"Not able to calc used traffic of {sub.__str__()}")
        raise error
    subTraffic = await sync_to_async(getattr)(sub, 'traffic')
    now = datetime.now()
    newStartDate = startDate = await sync_to_async(getattr)(sub, 'start_date')
    period = await sync_to_async(getattr)(sub, 'period')
    assignq = models.assign.objects.filter(subscribe=sub, enable=True)
    end = datetime(
        day=startDate.day,
        month=startDate.month,
        year=startDate.year
    ) + period
    if now > end:
        newStartDate = now
        async for assign in assignq.aiterator():
            await assign.adelete()
        usedTraffic = traffic(0)
    if enable:
        if usedTraffic > subTraffic:
            newEnable = False
    if enable != newEnable or startDate != newStartDate:
        sub.enable = newEnable
        sub.start_date = newStartDate
        await sub.asave()

async def acheck_node_traffic(nodeId):
    if not isinstance(nodeId, models.node):
        try:
            node = await models.node.objects.aget(id=nodeId)
        except models.node.DoesNotExist:
            return
    else:
        node = nodeId
    nodeTraffic = await sync_to_async(getattr)(node, 'max_traffic')
    service = NodeService(node)
    assignq = models.assign.objects.filter(
        node=node
    )
    newEnable = enable = await sync_to_async(getattr)(node, 'enable')
    now = datetime.now()
    period = await sync_to_async(getattr)(node, 'period')
    periodStart = await sync_to_async(getattr)(node, 'period_start')
    end = datetime(
        day=periodStart.day,
        month=periodStart.month,
        year=periodStart.year
    ) + period
    deletedAssigns = 0
    editedNodes = 0
    if now > end:
        deletedAssigns += await assignq.acount()
        await assignq.adelete()
    usedTrafficSum = traffic(0)
    async for assign in assignq.aiterator():
        report = await service.agetReportByAssign(assign)
        usedTrafficSum = usedTrafficSum + report.Traffic
    newEnable = usedTrafficSum < nodeTraffic
    if enable != newEnable:
        node.enable = newEnable
        await node.save()
        editedNodes += 1
        if not newEnable:
            await sync_to_async(check_all_subscriptions_assigns.delay)()

async def acheck_all_subscriptions_time_and_traffic():
    return await run_multiple_task(
        [
            acheck_subscription_time_and_traffic(sub) async for sub in models.subscribe.objects.all().aiterator()
        ]
    )

async def acheck_all_assigns():
    return await run_multiple_task(
        [
            acheck_assign_backend(assign) async for assign in models.assign.objects.filter(enable=True).aiterator()
        ]
    )

async def acheck_all_subscriptions_assigns():
        return await run_multiple_task(
            [
                acheck_subscription_assigns(sub) async for sub in models.subscribe.objects.all().aiterator()
            ]
        )

async def acheck_all_nodes_traffic():
    return await run_multiple_task(
        [
            acheck_node_traffic(node) async for node in models.node.objects.all().aiterator()
        ]
    )

async def acheck_all_nodes():
        return await run_multiple_task(
            [
                acheck_backend_assign(node) async for node in models.node.objects.filter(enable=True).aiterator()
            ]
        )


@shared_task
def check_all_assigns():
    return async_to_sync(acheck_all_assigns)()

@shared_task
def check_all_nodes():
    return async_to_sync(acheck_all_nodes)()

@shared_task
def check_all_nodes_traffic():
    return async_to_sync(acheck_all_nodes_traffic)()

@shared_task
def check_all_subscriptions_assigns():
    return async_to_sync(acheck_all_subscriptions_assigns)()

@shared_task
def check_all_subscriptions_time_and_traffic():
    return async_to_sync(acheck_all_subscriptions_time_and_traffic)()

@shared_task
def check_backend_assign(nodeId):
    return async_to_sync(acheck_backend_assign)(nodeId)

@shared_task
def check_assign_backend(assignid):
    return async_to_sync(acheck_assign_backend)(assignid)

@shared_task
def check_subscription_assigns(subid):
    return async_to_sync(acheck_subscription_assigns)(subid)
