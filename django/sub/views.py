from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from repo.models import subscribe, assign
from core.services import NodeService
from asgiref.sync import sync_to_async, async_to_sync
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiExample
from .titles import NormalTitle
from .configs import createEmptyConfig
from pymewess import EmptyConfig

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
        if not await subFilter.aexists():
            return HttpResponseNotFound()
        sub = await subFilter.afirst()
        asignsQ = assign.objects.filter(subscribe=sub)
        resp = ''
        async for i in asignsQ.aiterator():
            node = await sync_to_async(getattr)(i, 'node')
            nodeService = NodeService(node)
            assignStatus = await nodeService.aexists(i)
            if assignStatus :
                title = await NormalTitle(sub).normal()
                config = await nodeService.aconfig(i)
            else:
                title = "Creating config, reload this sub 1min later"
                config = EmptyConfig()
            config._set(name=title)
            url = config.url()
            resp += url

        resp += ''
        return HttpResponse(resp)
    return async_to_sync(view)()