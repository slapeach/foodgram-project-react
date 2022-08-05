from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.serializers import UserSerializer
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag"""
    slug = serializers.SlugField(
        max_length=200,
        validators=[
            UniqueValidator(
                queryset=Tag.objects.all(),
                message='Поле slug должно быть уникальным!'
            )
        ]
    )

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ingredient"""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForCreatingRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели IngredientInRecipe.
    Используется для создания рецепта.
    """
    id = serializers.IntegerField(source='ingredient_id')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeSerializer(serializers.HyperlinkedModelSerializer):
    """
    Сериализатор модели IngredientInRecipe.
    Применяется для вывода всех данных модели Ингредиент,
    которые есть в рецепте.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe для получение списка или одного рецепта.
    """
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_in_recipe', many=True
    )
    image = Base64ImageField(
        max_length=None, use_url=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients',
                  'name', 'image',
                  'text', 'cooking_time',
                  'is_favorited', 'is_in_shopping_cart'
                  )

    def get_is_favorited(self, obj):
        return obj.favorites.exists()

    def get_is_in_shopping_cart(self, obj):
        return obj.is_in_shopping_cart.exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe для создания рецепта.
    """
    author = serializers.ReadOnlyField(source='recipe.author')
    ingredients = IngredientForCreatingRecipeSerializer(
        source='ingredient_in_recipe', many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(
        max_length=None, use_url=True, required=True
    )
    name = serializers.CharField(max_length=200, required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time', 'author')

    def validate(self, attrs):
        tags = attrs['tags']
        ingredients = attrs['ingredient_in_recipe']
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Установленные в рецепте теги повторяются'
            )
        if len(ingredients) > 1:
            ingredient_id = ingredients[0]['ingredient_id']
            for ingredient in ingredients[1:]:
                if ingredient_id == ingredient['ingredient_id']:
                    raise serializers.ValidationError(
                        'Установленные в рецепте ингредиенты повторяются'
                    )
        return super().validate(attrs)

    def to_representation(self, instance):
        recipe = super().to_representation(instance)
        recipe = RecipeSerializer(instance).data
        return recipe

    def create_ingredient_in_recipe(self, recipe, ingredients_data):
        new_ingredients = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=ingredient_data['ingredient_id'],
                amount=ingredient_data['amount'],
            )
            for ingredient_data in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(new_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredient_in_recipe')
        recipe = Recipe.objects.create(
            author=self.context.get('request').user, **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredient_in_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredient_in_recipe')
        instance = super(RecipeCreateSerializer, self).update(
            instance, validated_data
        )
        instance.tags.set(tags)
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredient_in_recipe(instance, ingredients_data)
        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Favorite. Позволяет добавить рецепт в Избранное.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    image = Base64ImageField(
        source='recipe.image', max_length=None, use_url=True,
        required=False, read_only=True
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        extra_kwargs = {'recipe': {'write_only': True},
                        'user': {'write_only': True}}

    def validate(self, attrs):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('pk')
        )
        user = self.context.get('user')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в Избранном'
            )
        return super().validate(attrs)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ShoppingCart.
    Позволяет добавить рецепт в Список покупок.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    image = Base64ImageField(
        source='recipe.image', max_length=None, use_url=True,
        required=False, read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')
        extra_kwargs = {'recipe': {'write_only': True},
                        'user': {'write_only': True}}

    def validate(self, attrs):
        recipe = get_object_or_404(
            Recipe, pk=self.context.get('pk')
        )
        user = self.context.get('user')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в Избранном'
            )
        return super().validate(attrs)
