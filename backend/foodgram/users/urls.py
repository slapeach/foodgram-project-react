from django.urls import include, path
from rest_framework import routers

from .views import (APIChangePassword, APISendToken, SubscriptionViewSet,
                    UserViewSet)

app_name = 'users'

router = routers.DefaultRouter()
router.register(
    r'users/subscriptions', SubscriptionViewSet, basename='subscriptions'
)
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/token/login/', APISendToken.as_view(), name='get_token'),
    path(
        'users/set_password/', APIChangePassword.as_view(), name='set_password'
    ),
    path('', include(router.urls))
]
