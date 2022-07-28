from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import Ingredient, Tag, Recipe, Favorite, ShoppingCart

from .mixins import ListCreateDestroyMixin
from .permissions import IsAdminOrReadOnly
from .serializers import FavoriteRecipeSerializer, IngredientSerializer, RecipeSerializer, TagSerializer, ShoppingCartSerializer


class TagViewSet(ListCreateDestroyMixin):
    """Вьюсет сериализатора TagSerializer"""
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields = ['author', 'tags']

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='favorite')
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = FavoriteRecipeSerializer(
                data=request.data, context={'pk': pk, 'user': self.request.user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                recipe_id=pk, 
                user=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            user = self.request.user
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'Этого рецепта нет в Избранном'},
                    status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='shopping_cart')
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data=request.data, context={'pk': pk, 'user': self.request.user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                recipe_id=pk, 
                user=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            user = self.request.user
            recipe = get_object_or_404(Recipe, pk=pk)
            favorite = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if favorite:
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'Этого рецепта нет в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST)
