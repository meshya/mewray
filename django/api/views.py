from rest_framework.views import APIView
from repo import models
from .serializers import SubscriptionSerializer, SubscriptionCreateSerializer, SubscriptionListSerializer, ResponseSerializer
from django.http import JsonResponse, HttpResponse, HttpRequest, Http404
from asgiref.sync import async_to_sync, sync_to_async
from drf_spectacular.utils import extend_schema
from apikey.authentication import XManagerAuth
from core.tasks import check_subscription_assigns, check_backend_assign


async def makeResponse(serializer:ResponseSerializer, HttpStatus=202,**kwargs):
    export = await sync_to_async(getattr)(serializer, 'data')
    return JsonResponse(
        export,
        status = HttpStatus,
        **kwargs
    )

from django.db.models import Subquery


class SubscriptionsAPIView(APIView):
    authentication_classes = [
        XManagerAuth
    ]
    @async_to_sync
    @extend_schema(
        responses={
                200:ResponseSerializer[SubscriptionSerializer],
                404:ResponseSerializer[4]
            },
            # auth=[
                # 'XManagerKey'
            # ]
    )
    async def get(self, request, UserId):
        q = models.subscribe.objects.filter(api_pk=UserId)
        if not await q.aexists():
            return await makeResponse(status=4, HttpStatus=404)
        serializer = ResponseSerializer[SubscriptionSerializer](
            status=0,
            data=await q.afirst()
        )
        return await makeResponse(
                serializer,
                200
            )

    
    @async_to_sync
    @extend_schema(
        responses={
            204:ResponseSerializer,
            404:ResponseSerializer[4]
        }
    )
    async def delete(self, request, UserId):
        q = models.subscribe.objects.filter(api_pk=UserId)
        if not await q.aexists():
            return await makeResponse(
                ResponseSerializer[4](),
                HttpStatus=404
            )
        sub = await q.afirst()
        nodeq = models.node.objects.filter(
            id__in=Subquery(
                models.assign.objects.filter(
                    subscribe=sub
                )
            )
            )
        async for node in nodeq.aiterator():
            nodeId = await sync_to_async(lambda: node.id)
            await sync_to_async(check_backend_assign.delay)(nodeId)

        await q.adelete()
        return await makeResponse(
            ResponseSerializer(status=0),
            HttpStatus=204
        )


class SubscriptionsListAPIView(APIView):
    authentication_classes = [
        XManagerAuth
    ]
    @async_to_sync
    @extend_schema(
        request=SubscriptionCreateSerializer,
        responses={
            201:ResponseSerializer[SubscriptionSerializer],
            400:ResponseSerializer[3],
            404:ResponseSerializer[4]
        }
    )
    async def post(self, request:HttpRequest):
        serializer = SubscriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return await makeResponse(
                ResponseSerializer(
                    status=3
                ),
                HttpStatus=400
            )
        try:
            obj = await serializer.acreate(serializer.data)
        except Http404:
            return await makeResponse(
                ResponseSerializer(status=4),
                HttpStatus=404
            )
        await sync_to_async(check_subscription_assigns.delay)(obj.id)
        respSerializer = ResponseSerializer[SubscriptionSerializer](
            status=0,
            data=obj
        )
        return await makeResponse(
            respSerializer,
            HttpStatus=201
        )
    @async_to_sync
    @extend_schema(
        responses={
            200:ResponseSerializer[SubscriptionListSerializer],
            500:ResponseSerializer[2]
        }
    )
    async def get(self, request):
        try:
            objs = models.subscribe.objects.filter()
            all=[]
            async for i in objs.aiterator():
                all.append(i)
            serializer = ResponseSerializer[SubscriptionListSerializer](all)
        except:
            return await makeResponse(
                ResponseSerializer(
                    status=2
                ),
                HttpStatus=500
            )
        return await makeResponse(
            serializer,
            HttpStatus=200
        )

from apikey.exceptions import NoApiKey, InvalidApiKey

@async_to_sync
async def AuthErrorHandler(exc, context):
    if isinstance(exc, NoApiKey|InvalidApiKey):
        return await makeResponse(
            ResponseSerializer(
                status=1
            ),
            HttpStatus=401
        )
    return await makeResponse(
        ResponseSerializer[2](),
        HttpStatus=500
    )