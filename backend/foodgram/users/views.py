from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Subscription, User
from .serializers import (PasswordSerializer, SubscriptionSerializer,
                          TokenSerializer, UserRegistrationSerializer,
                          UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для urls 'users'.
    Позволяет получить список пользователей,
    профиль конкретного пользователя.
    """
    permission_classes = (AllowAny,)
    pagination_class = PageNumberPagination
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserSerializer
        return UserRegistrationSerializer

    @action(methods=['get'],
            detail=False,
            permission_classes=(IsAuthenticated,),
            url_path='me',)
    def user_data(self, request):
        """
        Метод для вывода данных текущего пользователя.
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'],
            detail=True,
            permission_classes=(AllowAny,),)
    def create_user(self, request):
        """
        Метод для регистрации пользователя.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post', 'delete'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='subscribe',)
    def subscribe(self, request, pk=None):
        """
        Метод для создания Подписки на автора,
        удаления Подписки на атвора.
        """
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data=request.data, context={
                    'pk': pk, 'user': self.request.user
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                author_id=pk,
                user=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            user = self.request.user
            author = get_object_or_404(User, pk=pk)
            subscription = Subscription.objects.filter(
                user=user, author=author
            )
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'Вы не были подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)


class APIChangePassword(APIView):
    """
    Вьюкласс для смены пароля пользователя.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=request.user.username
        )
        if check_password(
                serializer.validated_data['current_password'], user.password
        ):
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class APISendToken(APIView):
    """
    Вьюкласс для получения токена пользователем.
    """
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, email=serializer.validated_data['email']
        )
        if check_password(
                serializer.validated_data['password'], user.password):
            token = Token.objects.create(user=user)
            return Response(
                {'auth_token': str(token)}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Вьюсет для создания/удаления Подписки на автора."""
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination
    serializer_class = SubscriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('id',)

    def get_queryset(self):
        user = self.request.user
        queryset = Subscription.objects.filter(user=user)
        return queryset
