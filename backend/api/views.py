from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.authentication import (SessionAuthentication,
                                           TokenAuthentication)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from users.serializers import RecipeLiteSerializer

from .filters import IngredientFilter, RecipeFilter
from .models import (FavoritRecipe, Ingredient, IngredientForRecipe, Recipe,
                     ShoppingList, Tag)
from .permissions import OwnerOrAdminOrAuthenticatedOrReadOnly
from .serializers import (IngredientSerializer, RecipePostUpdateSerializer,
                          RecipeSerializer, TagSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny]


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [AllowAny]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [OwnerOrAdminOrAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'put', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        recipe = Recipe.objects.filter(author=self.request.user).first()
        serializer_class = self.get_serializer_class(to_represent=True)
        serializer = serializer_class(
            recipe,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        recipe = Recipe.objects.get(id=instance.id)
        serializer_class = self.get_serializer_class(to_represent=True)
        serializer = serializer_class(
            recipe,
            context={'request': request}
        )
        return Response(serializer.data)

    def get_serializer_class(self, **kwargs):
        if (kwargs.get('to_represent', False)
                or self.request.method in ['GET', 'DELETE']):
            return RecipeSerializer
        return RecipePostUpdateSerializer

    def _get_or_delete(self, request, model, messages):
        object = get_object_or_404(Recipe, pk=self.kwargs['pk'])
        existance = model.objects.filter(
            user=request.user,
            recipe=object
        ).exists()
        if request.method == 'GET':
            if not existance:
                model.objects.create(
                    user=request.user,
                    recipe=object
                )
                serializer = RecipeLiteSerializer(object)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
            else:
                raise ValidationError(
                    {"errors": messages['already_in']}
                )
        if request.method == 'DELETE':
            if existance:
                model.objects.get(
                    user=request.user,
                    recipe=object
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ValidationError(
                    {"errors": messages['not_in']}
                )

    @action(
        detail=True,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        messages = {
            'already_in': 'Already in your favorites',
            'not_in': 'Was not in your favorites',
        }
        return self._get_or_delete(request, FavoritRecipe, messages)

    @action(
        detail=True,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, *args, **kwargs):
        messages = {
            'already_in': 'Already in your shopping_cart',
            'not_in': 'Was not in your shopping_cart',
        }
        return self._get_or_delete(request, ShoppingList, messages)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        results = IngredientForRecipe.objects.filter(
            recipe__is_in_shopping_list__user=request.user
        ).select_related('recipe').select_related('ingredient')
        to_buy_list = defaultdict(int)
        for note in results:
            to_buy_list[(note.ingredient.name,
                         note.ingredient.measurements_unit)] += note.amount
        final_string = ''
        for ingredient, amount in to_buy_list.items():
            final_string += f'{ingredient[0]} - {amount}({ingredient[1]})\n'
        response = HttpResponse(final_string, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           ' filename="shop_list.txt"')
        return response
