import base64
import re

from django.core.files import base, images
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import APIException

from users.serializers import CustomUserSerializer

from .models import (FavoritRecipe, Ingredient, IngredientForRecipe, Recipe,
                     ShoppingList, Tag, TagForRecipe)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurements_unit")


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurements_unit = serializers.CharField(
        source='ingredient.measurements_unit'
    )

    class Meta:
        model = IngredientForRecipe
        fields = ("id", "name", "measurements_unit", "amount")


class FromBase64ToImg(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            __, filename, __, image_encoded = re.split(';|,|:', data)
            filename = '.'.join(filename.split('/'))
            image_decoded = base64.b64decode(image_encoded)
            content = base.ContentFile(image_decoded)
            data = images.ImageFile(content, filename)
        except APIException:
            raise serializers.ValidationError('Can not decode image')
        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "tags", "author", "ingredients", "is_favorited",
                  "is_in_shopping_cart", "name", "image", "text",
                  "cooking_time")

    def get_ingredients(self, obj):
        queryset = (IngredientForRecipe.objects.filter(recipe=obj).
                    select_related('ingredient'))
        serializer = IngredientForRecipeSerializer(queryset, many=True)
        return serializer.data

    def _is_fav_or_is_in_shop(self, model, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        if model.objects.filter(
            recipe=obj,
            user=self.context['request'].user
        ).exists():
            return True
        return False

    def get_is_favorited(self, obj):
        return self._is_fav_or_is_in_shop(FavoritRecipe, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._is_fav_or_is_in_shop(ShoppingList, obj)

    def to_internal_value(self):
        pass


class RecipePostUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        write_only=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        write_only=True
    )
    image = FromBase64ToImg()

    class Meta:
        model = Recipe
        fields = ("ingredients", "tags", "image", "name", "text",
                  "cooking_time")

    def _create_or_update_tags_and_ingredients(
        self, tags, ingredients, recipe, **kwargs
    ):
        if kwargs.get('update', False):
            TagForRecipe.objects.filter(recipe=recipe).delete()
            IngredientForRecipe.objects.filter(recipe=recipe).delete()

        for tag_id in tags:
            tag = get_object_or_404(Tag, id=tag_id)
            TagForRecipe.objects.create(tag=tag, recipe=recipe)

        for ingredient in ingredients:
            ingredient_id, amount = ingredient['id'], ingredient['amount']
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient_id)
            IngredientForRecipe.objects.create(
                ingredient=ingredient_obj,
                amount=amount,
                recipe=recipe
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        self._create_or_update_tags_and_ingredients(
            tags, ingredients, recipe
        )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        self._create_or_update_tags_and_ingredients(
            tags, ingredients, instance, update=True
        )

        return instance
