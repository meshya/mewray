from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('subscriptions/<str:UserId>/',
        views.SubscriptionsAPIView.as_view()
    ),
    path('subscriptions',
        views.SubscriptionsListAPIView.as_view()
    ),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
