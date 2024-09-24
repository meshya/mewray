from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('subscriptions/<int:pk>/', views.SubscriptionsAPIView.as_view()),
    path('subscriptions',views.SubscriptionsListAPIView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)