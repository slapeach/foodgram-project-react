import django_filters

from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для Recipe по автору и тегу"""
    author = django_filters.CharFilter(field_name='author__username')
    tags = django_filters.CharFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = [
            'tags', 'author',
        ]
