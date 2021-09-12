from rest_framework.exceptions import ValidationError, NotAuthenticated, NotAcceptable
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from djoser.views import UserViewSet

from .models import User, Subscription
from .serializers import CustomUserSerializer
from backend.settings import REST_FRAMEWORK


class CustomUserViewSet(UserViewSet):
    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        user_subscriptions = User.objects.filter(
            followed__user=self.request.user
        )
        serializer = self.get_serializer(user_subscriptions, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'delete'],
        url_path=(r'(?P<id>\d+)/subscribe'),
        url_name='subscribe',
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
                raise ValidationError("It's not allowed to subscribe on youself")
            if not existance:
                Subscription.objects.create(
                    user=request.user,
                    interesting_author=interesting_author
                )
                serializer = CustomUserSerializer(
                    interesting_author,
                    context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                raise NotAcceptable(detail='Such subscription already exists', code=status.HTTP_400_BAD_REQUEST)
                # return Response(status=status.HTTP_400_BAD_REQUEST)
                # raise APIException("Such subscription already exists")
        if request.method == 'DELETE':
            if existance:
                Subscription.objects.get(
                    user=request.user,
                    interesting_author=interesting_author
                ).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                raise NotAcceptable()
