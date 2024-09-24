from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('subscriptions/<int:pk>/', csrf_exempt(
        views.SubscriptionsAPIView.as_view())
        ),
    path('subscriptions',csrf_exempt(
        views.SubscriptionsListAPIView.as_view()))
]

urlpatterns = format_suffix_patterns(urlpatterns)