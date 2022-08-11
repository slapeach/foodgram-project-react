import django_filters

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='get_ingredient_by_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def get_ingredient_by_name(self, queryset, name, value):
        if value:
            return queryset.filter(name__startswith=value)
        return queryset


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для Recipe по автору, тегу, избранному, списку покупок"""
    author = django_filters.NumberFilter(method='get_author_recipes')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'tags', 'author'
        ]

    def get_author_recipes(self, queryset, name, value):
        if value:
            return queryset.filter(author_id=value)
        return queryset

    def get_is_favorited(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            favorites = list(
                Favorite.objects.filter(
                    user=self.request.user).values_list('recipe_id', flat=True)
            )
            fav_queryset = queryset.filter(id__in=favorites)
            return fav_queryset
        else:
            return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            shopping_cart = list(
                ShoppingCart.objects.filter(
                    user=self.request.user).values_list('recipe_id', flat=True)
            )
            sc_queryset = queryset.filter(id__in=shopping_cart)
            return sc_queryset
        else:
            return queryset
