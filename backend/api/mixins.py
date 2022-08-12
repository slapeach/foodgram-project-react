from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.mixins import (CreateModelMixin, DestroyModelMixin,
                                   ListModelMixin)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from recipes.models import Recipe


class ListCreateDestroyMixin(ListModelMixin, CreateModelMixin,
                             DestroyModelMixin, GenericViewSet):
    """Миксин на создание, удаление и получение списка"""
    search_fields = ('name',)
    lookup_field = 'slug'


class AddDelRecipeViewMixin:
    """
    Миксин для добавления рецепта в Избранное/Список покупок,
    удаления рецепта из Избранного/Списка покупок.
    """

    def add_del_obj(self, obj_id, serializer, queryset):
        user = self.request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if self.request.method == 'POST':
            serializer = serializer(
                data=self.request.data, context={
                    'pk': obj_id, 'user': self.request.user
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                recipe_id=obj_id,
                user=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            user = self.request.user
            recipe = get_object_or_404(Recipe, pk=obj_id)
            is_favorited_or_in_sc = queryset.filter(user=user, recipe=recipe)
            if is_favorited_or_in_sc.exists:
                is_favorited_or_in_sc.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
