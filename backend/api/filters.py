import django_filters
from django_filters.rest_framework import FilterSet

from .models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.BooleanFilter(
        field_name='is_favorite_for_users',
        method='get_is_favorite'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_list',
        method='get_is_in_shopping_list'
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def get_is_favorite(self, queryset, name, value):
        if value:
            recipes_in_favorits = '__'.join([name, 'user'])
            return queryset.filter(**{recipes_in_favorits: self.request.user})
        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        if value:
            recipes_in_shopping_list = '__'.join([name, 'user'])
            return queryset.filter(
                **{recipes_in_shopping_list: self.request.user}
            )
        return queryset
