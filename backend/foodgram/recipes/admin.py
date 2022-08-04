from django.contrib import admin

from users.models import User

from .models import Ingredient, IngredientInRecipe, Recipe, Tag


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'email', 'username',
                    'first_name', 'last_name',
                    'password', 'role')
    list_filter = ('email', 'username',)


class IngredientAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('author', 'name', 'is_favorited_count')
    list_filter = ('author', 'name', 'tags')

    def is_favorited_count(self, obj):
        return obj.favorites.count()
    is_favorited_count.short_description = u'в избранном'


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
