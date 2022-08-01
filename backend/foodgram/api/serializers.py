import json
from django.shortcuts import get_object_or_404
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from recipes.models import Ingredient, IngredientInRecipe, Tag, Recipe, Favorite, ShoppingCart
from users.serializers import UserSerializer


class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.

    Heavily based on
    https://github.com/tomchristie/django-rest-framework/pull/1268

    Updated for Django REST framework 3.
    """

    def to_internal_value(self, data):
        from django.core.files.base import ContentFile
        import base64
        import six
        import uuid

        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension

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
    """Сериализатор модели Ingredient"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeSerializer(serializers.HyperlinkedModelSerializer):
    """Сериализатор модели Ingredient"""
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe"""
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(source='ingredientinrecipe_set', many=True)
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
        if obj.favorites.exists():
            return True
        return False
    
    def get_is_in_shopping_cart(self, obj):
        if obj.is_in_shopping_cart.exists():
            return True
        return False


class RecipeCreateSerializer(WritableNestedModelSerializer, serializers.ModelSerializer):
    ingredients = IngredientForCreatingRecipeSerializer(many=True, required=True)
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
                  'text', 'cooking_time',)
        extra_kwargs = {'author': {'write_only': True}}

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context.get('request').user, **validated_data)
        recipe.tags.set(tags)
        for ingredient_data in ingredients_data:
            ingredient = ((list(ingredient_data.items())[0])[1])
            amount = ((list(ingredient_data.items())[1])[1])
            IngredientInRecipe.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)
        return recipe


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    image = Base64ImageField(
        max_length=None, use_url=True, read_only=True
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
    """Сериализатор модели ShoppingCart"""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')
    image = Base64ImageField(
        max_length=None, use_url=True, read_only=True
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