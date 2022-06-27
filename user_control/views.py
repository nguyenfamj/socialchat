import jwt
from .models import Jwt, CustomUser, Favorite, UserProfile
from datetime import datetime, timedelta
from django.conf import settings
import random
import string
import re

from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import LoginSerializer, RegisterSerializer, RefreshSerializer, UserProfileSerializer
from django.contrib.auth import authenticate
from .authentication import Authentication
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q, Count, OuterRef

from socialchat.custom_auth import IsAuthenticatedCustom


# Create your views here.
def get_random(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def get_access_token(payload):
    return jwt.encode({"exp": datetime.now() + timedelta(minutes=5), **payload}, settings.SECRET_KEY, 'HS256')


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
            return Response({"success": False, "message": "Invalid username or password"}, status="400")

        Jwt.objects.filter(user_id=user.id).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(
            user_id=user.id, access=access.decode(), refresh=refresh.decode())

        return Response({"success": True, "access": access, "refresh": refresh}, status="200")


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.pop("username")

        CustomUser.objects.create_user(
            username=username, **serializer.validated_data)

        return Response({"success": True, "message": "User created successfully"}, status=201)


class RefreshView(APIView):
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_tokens = Jwt.objects.get(
                refresh=serializer.validated_data["refresh"])
        except Jwt.DoesNotExist:
            return Response({"success": False, "message": "Refresh token not found"}, status=400)

        if not Authentication.verify_token(serializer.validated_data["refresh"]):
            return Response({"success": False, "message": "Token is invalid or has expired"}, status=401)

        access = get_access_token({"user_id": user_tokens.user.id})
        refresh = get_refresh_token()

        user_tokens.access = access.decode()
        user_tokens.refresh = refresh.decode()
        user_tokens.save()

        return Response({"success": True, "access": access, "refresh": refresh})


class UserProfileView(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedCustom,)

    def get_queryset(self):
        # if self.request.method.lower() != "get":
        #     return self.queryset

        data = self.request.query_params.dict()
        # data.pop("page", None)
        keyword = data.pop("keyword", None)

        if keyword:
            search_fields = (
                "user__username", "first_name", "last_name", "user__email"
            )
            query = self.get_query(keyword, search_fields)

            # try:
            #     return self.queryset.filter(query).filter(**data).exclude(Q(user_id=self.request.user.id) | Q(user__is_superuser=True)).annotate(fav_count=Count(self.user_favorites_query(self.request.user))).order_by("-fav_count")
            # except Exception as e:
            #     raise Exception(e)
            return self.queryset.filter(query).distinct()
        return self.queryset

        # return self.queryset.filter(**data).exclude(Q(user_id=self.request.user.id) |
        #                                             Q(user__is_superuser=True)).annotate(fav_count=Count(self.user_favorites_query(self.request.user))).order_by("-fav_count")

    # @staticmethod
    # def user_favorites_query(user):
    #     try:
    #         return user.user_favorites.favorite.filter(id=OuterRef("user_id")).values("pk")
    #     except Exception:
    #         return []

    @staticmethod
    def get_query(query_string, search_fields):
        query = None
        terms = UserProfileView.normalize_query(query_string)
        for term in terms:
            or_query = None
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    @staticmethod
    def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]
