from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """Модель Ингредиент"""
    name = models.CharField(
        max_length=200,
        verbose_name='Ингредиент',
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Единица измерения',
        help_text='Введите единицу измерения ингредиента'
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'ingredient'
        verbose_name_plural = 'ingredients'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель Тег"""
    name = models.CharField(
        unique=True,
        max_length=200,
        verbose_name='Название тега',
        help_text='Введите название тега'
    )
    color = models.CharField(
        unique=True,
        max_length=7,
        verbose_name='Цвет тега',
        help_text='Введите цветовой HEX-код (например, #49B64E).'
    )
    slug = models.SlugField(
        unique=True,
        max_length=200,
        verbose_name='Слаг тега',
        help_text='Введите слаг тега'
    )

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель Рецепт"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
        help_text='Укажите автора рецепта'
    )

    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта'
    )

    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Фото готового блюда',
        help_text='Загрузите фото к рецепту'
    )

    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
        related_name='recipes',
        help_text='Выберите ингредиенты, укажите кол-во'
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes',
        help_text='Установите теги(и)'
    )

    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное время приготовления - 1 мин.'),
        ],
        verbose_name='Время приготовления',
        help_text='Введите время приготовления (в минутах)'
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'recipe'
        verbose_name_plural = 'recipes'

    def __str__(self):
        return self.text


class IngredientInRecipe(models.Model):
    """Модель Ингредиента в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_in_recipe',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient',
    )

    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, 'Минимальное количество ингредиента - 1'),
        ],
        verbose_name='Количество ингредиента',
        help_text='Введите кол-во ингрединта'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe',
            ),
        ]
        verbose_name = 'ingredient'
        verbose_name_plural = 'ingredients'


class Favorite(models.Model):
    """Модель Избранное"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ]
        verbose_name = 'favorite'
        verbose_name_plural = 'favorites'


class ShoppingCart(models.Model):
    """Модель Список покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart',
            ),
        ]
        verbose_name = 'shopping cart'
        verbose_name_plural = 'shopping carts'
