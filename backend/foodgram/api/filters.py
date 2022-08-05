import django_filters

from recipes.models import Favorite, Recipe, ShoppingCart


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для Recipe по автору и тегу"""
    author = django_filters.CharFilter(field_name='author__username')
    tags = django_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filters.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'tags', 'author',
        ]

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
