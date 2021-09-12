from djoser.serializers import UserSerializer
from rest_framework import serializers

from .models import Subscription


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        if Subscription.objects.filter(
            interesting_author__id=obj.id,
            user=self.context['request'].user
        ).exists():
            return True
        return False
