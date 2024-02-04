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
from .serializers import IngredientSerializer, RecipeSerializer, TagSerializer
from .serve_functions import add_file_to_response, form_shop_list


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
    serializer_class = RecipeSerializer
    permission_classes = [OwnerOrAdminOrAuthenticatedOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, *args, **kwargs):
        return self._create_link(request, FavoritRecipe)

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        return self._delete_link(request, FavoritRecipe)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, *args, **kwargs):
        return self._create_link(request, ShoppingList)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        return self._delete_link(request, ShoppingList)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        results = IngredientForRecipe.objects.filter(
            recipe__is_in_shopping_list__user=request.user
        ).select_related('recipe').select_related('ingredient')
        data = form_shop_list(results)
        response = add_file_to_response(data, 'text/plain')
        return response

    def _create_link(self, request, model):
        object = get_object_or_404(Recipe, pk=self.kwargs['pk'])
        exists = model.objects.filter(
            user=request.user,
            recipe=object
        ).exists()
        if not exists:
            model.objects.create(
                user=request.user,
                recipe=object
            )
            serializer = RecipeLiteSerializer(object)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        raise ValidationError({"errors": 'Already exists'})

    def _delete_link(self, request, model):
        model.objects.filter(
            user=request.user,
            recipe__pk=self.kwargs['pk']
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
