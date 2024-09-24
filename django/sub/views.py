from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from repo.models import subscribe, assign
from core.services import NodeService
from asgiref.sync import sync_to_async

async def subcribeView(request:HttpRequest, subid):
    subFilter = subscribe.objects.filter(view_pk=subid)
    if await subFilter.aexists():
        sub = await subFilter.afirst()
        asignsQ = assign.objects.filter(subscribe=sub)
        resp = ''
        async for i in asignsQ.aiterator():
            node = await sync_to_async(getattr)(i, 'node')
            nodeService = NodeService(node)
            resp += "" + await nodeService.agetUrlByAssign(i.uuid, name='test') + ""
        resp += ''
        return HttpResponse(resp)
    return HttpResponseNotFound()