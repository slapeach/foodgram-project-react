from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Exists
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,)
from rest_framework.response import Response

from recipes.models import (Ingredient, IngredientInRecipe,
                            Tag, Recipe, Favorite, ShoppingCart)

from .filters import RecipeFilter
from .mixins import ListCreateDestroyMixin
from .permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeCreateSerializer,
                          TagSerializer, ShoppingCartSerializer)


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
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        user = self.request.user
        favorites = list(
            Favorite.objects.filter(user=user).values_list(
                'recipe_id', flat=True
            )
        )
        shopping_cart = list(
            ShoppingCart.objects.filter(user=user).values_list(
                'recipe_id', flat=True
            )
        )
        if is_favorited:
            queryset = queryset.filter(id__in=favorites)
        if is_in_shopping_cart:
            queryset = queryset.filter(id__in=shopping_cart)
        if is_favorited and is_in_shopping_cart:
            queryset = queryset.filter(id__in=favorites)
            queryset = queryset.filter(id__in=shopping_cart)
        return queryset

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='favorite')
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = FavoriteRecipeSerializer(
                data=request.data, context={
                    'pk': pk, 'user': self.request.user
                }
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
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data=request.data, context={
                    'pk': pk, 'user': self.request.user
                }
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

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__is_in_shopping_cart__user=self.request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(total=Sum('amount'))

        shopping_cart = '\n'.join([
            f'{ingredient["ingredient__name"]} - {ingredient["total"]}'
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ])
        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
