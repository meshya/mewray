from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from repo.models import subscribe, assign
from core.services import NodeService
from asgiref.sync import sync_to_async, async_to_sync
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiExample
from .titles import NormalTitle

@extend_schema(
    responses={
        200: str,
    },
    examples=[
        OpenApiExample(
            'Example',
            value='vless://......',
            response_only=True,
            status_codes=['200']
        )
    ],
    auth=[],
    description="Returns config urls of this user, ATTENTION: use ViewId of Subscriptions as subid"
)
@api_view(['GET'])
def subcribeView(request:HttpRequest, ViewId):
    async def view():
        subFilter = subscribe.objects.filter(view_pk=ViewId)
        if await subFilter.aexists():
            sub = await subFilter.afirst()
            asignsQ = assign.objects.filter(subscribe=sub)
            resp = ''
            async for i in asignsQ.aiterator():
                node = await sync_to_async(getattr)(i, 'node')
                nodeService = NodeService(node)
                title = await NormalTitle(sub).normal()
                resp += "" + await nodeService.agetUrlByAssign(i.uuid, name=title) + ""
            resp += ''
            return HttpResponse(resp)
        return HttpResponseNotFound()
    return async_to_sync(view)()