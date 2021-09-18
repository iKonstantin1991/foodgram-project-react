import django_filters
from django_filters.rest_framework import FilterSet

from .models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = django_filters.CharFilter(field_name='tags__slug')
    is_favorited = django_filters.NumberFilter(
        field_name='is_favorite_for_users',
        method='get_is_favorite'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name='is_in_shopping_list',
        method='get_is_in_shopping_list'
    )

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]

    def get_is_favorite(self, queryset, name, value):
        if value == 1:
            lookup = '__'.join([name, 'user'])
            return queryset.filter(**{lookup: self.request.user})
        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        if value == 1:
            lookup = '__'.join([name, 'user'])
            return queryset.filter(**{lookup: self.request.user})
        return queryset
