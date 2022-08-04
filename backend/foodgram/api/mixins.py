from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.viewsets import GenericViewSet


class ListCreateDestroyMixin(ListModelMixin, CreateModelMixin,
                             DestroyModelMixin, GenericViewSet):
    """Миксин на создание, удаление и получение списка"""
    search_fields = ('name',)
    lookup_field = 'slug'
