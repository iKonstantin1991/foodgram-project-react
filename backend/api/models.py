import datetime as dt

from django.contrib.auth import get_user_model
from django.db import models
from pytz import timezone

from backend import settings

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)  # Should check
    slug = models.SlugField(max_length=200)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'color', 'slug'],
                name='uniq_all_fields'
            )
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    measurements_unit = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name}({self.measurements_unit})'


def rename_with_date_and_save(instance, filename):
    now = (dt.datetime.now(tz=timezone(settings.TIME_ZONE))
           .strftime(r'%Y_%m_%d-%H_%M_%S'))
    name, extension = filename.split('.')
    filename = name + f'_{now}.' + extension
    return f'recipes/{filename}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=50)
    text = models.TextField(
        max_length=300,
    )
    image = models.ImageField(
        upload_to=rename_with_date_and_save,
        blank=True,
        null=True
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagForRecipe',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientForRecipe',
        related_name='recipes',
    )
    cooking_time = models.IntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class TagForRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='uniq_pair_recipe_tag'
            )
        ]

    def __str__(self):
        return f'Pair of {self.tag}, {self.recipe}'


class IngredientForRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.IntegerField()

    class Meta:
        ordering = ['recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='uniq_pair_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'Need {self.amount} of {self.ingredient} for {self.recipe}'


class FavoritRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorite_for_users'
    )

    class Meta:
        ordering = ['user__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniq_pair_user_recipe_fav'
            )
        ]

    def __str__(self):
        return f'{self.user} likes {self.recipe}'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes_in_shopping_list'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_list'
    )
    # def __init__(self):
    #     super().__init__()
    #     self.user.related_name = 'recipes_in_shopping_list'
    #     self.recipe.related_name = 'is_in_shopping_list'

    class Meta:
        ordering = ['user__last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniq_pair_user_recipe_shop'
            )
        ]

    def __str__(self):
        return f'{self.recipe} is in shopping list of {self.user}'
