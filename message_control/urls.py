from django.urls import path, include
from rest_framework.routers import DefaultRouter
from.views import GenericFileUploadView, MessageView

router = DefaultRouter(trailing_slash=False)

router.register("file-upload", GenericFileUploadView)
router.register("message", MessageView)

urlpatterns = [
    path("", include(router.urls))
]
