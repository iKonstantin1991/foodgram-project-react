from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    email = models.EmailField('email address', max_length=254, unique=True)
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


User = get_user_model()


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    interesting_author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed'
    )

    def __str__(self):
        return f'{self.user} follows {self.interesting_author}'
