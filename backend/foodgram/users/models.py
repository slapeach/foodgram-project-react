from django.contrib.auth.models import AbstractUser
from django.db import models

GUEST = 'guest'
USER = 'user'
ADMIN = 'admin'
ROLE_CHOICES = (
    (GUEST, 'guest'),
    (USER, 'user'),
    (ADMIN, 'admin'),
)


class User(AbstractUser):
    """Модель Пользователь"""
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Адрес электронной почты',
        help_text='Это поле должно быть уникальным'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Логин пользователя',
        help_text='Это поле должно быть уникальным'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя',
        help_text='Введите имя пользователя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия пользователя',
        help_text='Введите фамилию пользователя'
    )
    password = models.CharField(
        max_length=150,
        verbose_name='Пароль от аккаунта',
        help_text='Введите пароль'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Роль пользователя'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_guest(self):
        return self.role == GUEST

    @property
    def is_user(self):
        return self.role == USER

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email', 'username'],
                                    name='unique_user')
        ]
        ordering = ['username']
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель Подписка на автора"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_subscription')
        ]
        verbose_name = 'subscription'
        verbose_name_plural = 'subscriptions'
