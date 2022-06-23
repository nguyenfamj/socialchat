from rest_framework.permissions import BasePermission
from django.utils import timezone


class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, view):
        from user_control.views import decode_jwt
        user = decode_jwt(request.META["HTTP_AUTHORIZATION"])

        if not user:
            return False

        request.user = user
        if request.user and request.user.is_authenticated:
            from user_control.models import CustomUser
            CustomUser.objects.filter(id=request.user.id).update(
                is_online=timezone.now())
            return True
        return False
