from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from repo.models import subscribe, assign
from core.services import NodeService, AssignNotSynced
from asgiref.sync import sync_to_async, async_to_sync
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema, OpenApiExample
from .designers import Designer
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
    return async_to_sync(renderSub)(request, ViewId)

async def renderSub(request, viewId):
    subFilter = subscribe.objects.filter(view_pk=viewId)
    if not await subFilter.aexists():
        return HttpResponseNotFound()
    sub = await subFilter.afirst()
    return await Designer(sub).design()
