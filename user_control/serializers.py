from rest_framework import serializers
from .models import UserProfile, CustomUser
from message_control.serializers import GenericFileUploadSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        exclude = ("password",)


class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    user_id = serializers.CharField(write_only=True)
    profile_picture = GenericFileUploadSerializer(read_only=True)
    profile_picture_id = serializers.IntegerField(
        write_only=True, required=False)
    unseen = serializers.SerializerMethodField("get_unseen_count")

    class Meta:
        model = UserProfile
        fields = "__all__"

    def get_unseen_count(self, obj):
        try:
            user_id = self.context["request"].user.id
        except Exception as e:
            user_id = None

        from message_control.models import Message
        messages = Message.objects.filter(
            sender_id=obj.user.id, receiver_id=user_id, is_read=False).distinct()

        return messages.count()


class FavoriteSerializer(serializers.Serializer):
    favorite_id = serializers.IntegerField()
