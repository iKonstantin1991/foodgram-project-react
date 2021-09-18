from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.authentication import (SessionAuthentication,
                                           TokenAuthentication)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import CustomUserSerializer, SubscriptionsUserSerializer


class CustomUserViewSet(UserViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    @action(
        methods=["get"],
        detail=False,
        serializer_class=SubscriptionsUserSerializer,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request, *args, **kwargs):
        user_subscriptions = User.objects.filter(
            followed__user=self.request.user
        )
        page = self.paginate_queryset(user_subscriptions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['get', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        interesting_author = get_object_or_404(User, id=self.kwargs['id'])
        existance = Subscription.objects.filter(
            user=request.user,
            interesting_author=interesting_author
        ).exists()
        if request.method == 'GET':
            if request.user == interesting_author:
                raise ValidationError(
                    {"errors": "It's not allowed to subscribe on youself"}
                )
            if not existance:
                Subscription.objects.create(
                    user=request.user,
                    interesting_author=interesting_author
                )
                serializer = CustomUserSerializer(
                    interesting_author,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                raise ValidationError(
                    {"errors": "Such subscription already exists"}
                )
        if request.method == 'DELETE':
            if existance:
                Subscription.objects.get(
                    user=request.user,
                    interesting_author=interesting_author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise ValidationError(
                    {"errors": "Such subscription doesn't exist"}
                )
