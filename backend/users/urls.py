from django.urls import include, path
from rest_framework import routers

from .views import APIChangePassword, SubscriptionViewSet, UserViewSet

app_name = 'users'

router = routers.DefaultRouter()
router.register(
    r'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path(
        'users/set_password/', APIChangePassword.as_view(), name='set_password'
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
]
