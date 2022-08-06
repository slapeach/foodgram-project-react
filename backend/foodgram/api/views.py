from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated

from recipes.models import (Favorite, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingCart, Tag)
from .filters import RecipeFilter
from .mixins import AddDelRecipeViewMixin, ListCreateDestroyMixin
from .permissions import IsAdminOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)


class TagViewSet(ListCreateDestroyMixin):
    """
    Вьюсет для urls 'tags'.
    Обеспечивает получение списка тегов/одного тега.
    """
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для urls 'ingredients'.
    Обеспечивает получение списка ингредиентов/одного ингредиента.
    Позволяет осуществить поиск ингредиента по названию.
    """
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet, AddDelRecipeViewMixin):
    """
    Вьюсет для urls 'recipes'.
    Позволяет получить список рецептов/рецепт, создать,
    отредактировать рецепт; добавить рецепт в Избранное
    и/или Список покупок; выгрузить Список покупок.
    Настроена фильтрация по тегу и автору рецепта.
    """
    queryset = Recipe.objects.all()
    permission_classes = [AllowAny]
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='favorite',)
    def favorite(self, request, pk=None):
        """
        Метод для добавления рецепта в Избранное,
        удаления рецепта из Избранного.
        """
        serializer = FavoriteRecipeSerializer
        queryset = Favorite.objects.all()
        return self.add_del_obj(
            self, pk, serializer, queryset
        )

    @action(methods=['POST', 'DELETE'],
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """
        Метод для добавления рецепта в Список покупок,
        удаления рецепта из Списка покупок.
        """
        serializer = ShoppingCartSerializer
        queryset = ShoppingCart.objects.all()
        return self.add_del_obj(
            self, pk, serializer, queryset
        )

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """
        Метод для вывода ингредиентов из Списка покупок.
        Количество ингредиентов суммируется.
        Данные выводятся в файле с расширением .txt
        """
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
