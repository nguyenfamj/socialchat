import jwt
from .models import Jwt, CustomUser, Favorite
from datetime import datetime, timedelta
from django.conf import settings
import random
import string

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import LoginSerializer, RegisterSerializer, RefreshSerializer
from django.contrib.auth import authenticate
from .authentication import Authentication


# Create your views here.
def get_random(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_access_token(payload):
    return jwt.encode({"exp": datetime.now() + timedelta(minute=5), **payload}, settings.SECRET_KEY, 'HS256')


def get_refresh_token():
    return jwt.encode({"exp": datetime.now() + timedelta(days=365), "data": get_random(10)}, settings.SECRET_KEY, 'HS256')


def decode_jwt(bearer):
    if not bearer:
        return None

    token = bearer[7:]
    decoded = jwt.decode(token, settings.SECRET_KEY)
    if decoded:
        try:
            return CustomUser.objects.get(id=decoded["user_id"])
        except Exception:
            return None


class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'], password=serializer.validated_data['password'])

        if not user:
            return Response({"error": "Invalid username or password"}, status="400")

        Jwt.objects.filter(user_id=user.id).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(
            user_id=user.id, access=access.decode(), refresh=refresh.decode())

        return Response({"access": access, "refresh": refresh}, status="200")
