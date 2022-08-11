from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe
from .models import Subscription, User


class LimitedListSerializer(serializers.ListSerializer):
    """Сериализатор для ограничения выдачи рецептов в подписках"""

    def to_representation(self, data):
        data = data.all()[:3]
        return super(LimitedListSerializer, self).to_representation(data)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели User"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username', 'email',
            'first_name', 'last_name',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj).exists()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор модели User для регистрации пользователя"""

    class Meta:
        model = User
        fields = (
            'id',
            'username', 'email',
            'first_name', 'last_name',
            'password',
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordSerializer(serializers.ModelSerializer):
    """Сериализатор модели User для смены пароля"""
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ('current_password', 'new_password')


class RecipeSimpleSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe вывода данных о рецепте"""

    class Meta:
        list_serializer_class = LimitedListSerializer
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор модели Subscription для создания подписки."""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSimpleSerializer(
        source='author.recipes', many=True, read_only=True
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        extra_kwargs = {'author': {'write_only': True},
                        'user': {'write_only': True}}

    def validate(self, attrs):
        author = get_object_or_404(
            User, pk=self.context.get('pk')
        )
        user = self.context.get('user')
        if author.id == user.id:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )
        return super().validate(attrs)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        if request.method in ['POST']:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        if request.method in ['GET']:
            return Subscription.objects.filter(
                user=request.user, author=obj.author).exists()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author.id).count()
