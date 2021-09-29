import base64
import re

from django.core.files import base, images
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError

from users.serializers import CustomUserSerializer

from .models import (FavoritRecipe, Ingredient, IngredientForRecipe, Recipe,
                     ShoppingList, Tag, TagForRecipe)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")
        read_only_fields = ("id", "name", "color", "slug")

    def to_internal_value(self, data):
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientForRecipe
        fields = ("id", "name", "measurement_unit", "amount")

    def to_internal_value(self, data):
        return data


class FromBase64ToImg(serializers.ImageField):
    def to_internal_value(self, data):
        try:
            __, filename, __, image_encoded = re.split(';|,|:', data)
            filename = '.'.join(filename.split('/'))
            image_decoded = base64.b64decode(image_encoded)
            content = base.ContentFile(image_decoded)
            data = images.ImageFile(content, filename)
        except APIException:
            raise serializers.ValidationError(
                {'errors': 'Can not decode image'}
            )
        return data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = FromBase64ToImg()
    ingredients = IngredientForRecipeSerializer(
        source='ingredientforrecipe_set',
        many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "tags", "author", "ingredients", "is_favorited",
                  "is_in_shopping_cart", "name", "image", "text",
                  "cooking_time")

    def if_ids_repeated(self, value):
        ids_request_set = set(value)
        if not len(ids_request_set) == len(value):
            raise ValidationError(
                {'errors': 'Check for repeated values'}
            )

    def if_ids_dont_exist(self, value, model):
        ids_request_set = set(value)
        queryset = model.objects.all().only('id')
        ids_from_base_set = {note.id for note in queryset}
        if not ids_request_set.issubset(ids_from_base_set):
            raise ValidationError(
                {'errors': 'Some values do not exist'}
            )

    def validate_tags(self, value):
        self.if_ids_repeated(value)
        self.if_ids_dont_exist(value, Tag)
        return value

    def validate_ingredients(self, value):
        ids_list = [note['id'] for note in value]
        self.if_ids_repeated(ids_list)
        self.if_ids_dont_exist(ids_list, Ingredient)
        return value

    def create_tags(self, tags, recipe):
        try:
            for tag_id in tags:
                tag = get_object_or_404(Tag, id=tag_id)
                TagForRecipe.objects.create(tag=tag, recipe=recipe)
        except APIException:
            raise serializers.ValidationError(
                {'errors': 'One or more tags does not exist'}
            )

    def update_tags(self, tags, recipe):
        TagForRecipe.objects.filter(recipe=recipe).delete()
        self.create_tags(tags, recipe)

    def create_ingredients(self, ingredients, recipe):
        try:
            for ingredient in ingredients:
                ingredient_id, amount = ingredient['id'], ingredient['amount']
                ingredient_obj = get_object_or_404(
                    Ingredient, id=ingredient_id
                )
                IngredientForRecipe.objects.create(
                    ingredient=ingredient_obj,
                    amount=amount,
                    recipe=recipe
                )
        except APIException:
            raise serializers.ValidationError(
                {'errors': 'One or more ingredients does not exist'}
            )

    def update_ingredients(self, ingredients, recipe):
        IngredientForRecipe.objects.filter(recipe=recipe).delete()
        self.create_ingredients(ingredients, recipe)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientforrecipe_set')

        recipe = Recipe.objects.create(**validated_data)

        self.create_tags(tags, recipe)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientforrecipe_set')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        self.update_tags(tags, instance)
        self.update_ingredients(ingredients, instance)

        return instance

    def _is_in_list(self, model, obj):
        if not self.context['request'].user.is_authenticated:
            return False
        if model.objects.filter(
            recipe=obj,
            user=self.context['request'].user
        ).exists():
            return True
        return False

    def get_is_favorited(self, obj):
        return self._is_in_list(FavoritRecipe, obj)

    def get_is_in_shopping_cart(self, obj):
        return self._is_in_list(ShoppingList, obj)
