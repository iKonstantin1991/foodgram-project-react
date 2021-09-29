from django.contrib import admin

from .models import (FavoritRecipe, Ingredient, IngredientForRecipe, Recipe,
                     ShoppingList, Tag, TagForRecipe)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "color", "slug")
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "author", "in_favorites")
    search_fields = ("name", "author")
    list_filter = ("author", "name", "tags")
    empty_value_display = "-empty-"

    def in_favorites(self, obj):
        return obj.is_favorite_for_users.all().count()


@admin.register(TagForRecipe)
class TagForRecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "tag")
    search_fields = ("recipe", "tag")
    list_filter = ("recipe", "tag")


@admin.register(IngredientForRecipe)
class IngredientForRecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "recipe", "ingredient", "amount")
    search_fields = ("recipe", "ingredient")
    list_filter = ("recipe", "ingredient")


@admin.register(FavoritRecipe)
class FavoritRecipeAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "recipe")
    search_fields = ("user", "recipe")
    list_filter = ("user", "recipe")


@admin.register(ShoppingList)
class ShoppingListAdmin(FavoritRecipeAdmin):
    pass
