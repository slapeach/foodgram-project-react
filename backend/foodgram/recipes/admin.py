from django.contrib import admin

from .models import Ingredient, IngredientInRecipe, Tag, Recipe
from users.models import User


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1

class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'email', 'username',
                    'first_name', 'last_name',
                    'password', 'role')
    search_fields = ('username', 'email')


class IngredientAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')


class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('author', 'name')
    list_filter = ('author', 'name', 'tags')


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
