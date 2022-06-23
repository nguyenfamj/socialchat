from rest_framework.viewsets import ModelViewSet
from django.conf import settings
from socialchat.custom_auth import IsAuthenticatedCustom
from .serializers import GenericFileUpload, GenericFileUploadSerializer, Message, MessageAttachment, MessageSerializer
from rest_framework.response import Response
from django.db.models import Q
import requests
import json

# Create your views here.


def handle_request(serializer_data):
    notification = {
        "message": serializer_data.get("message"),
        "from": serializer_data.get("sender"),
        "to": serializer_data.get("receiver").get("id"),
    }
    headers = {
        "Content-Type": "application/json",
    }
    try:
        requests.post(settings.SOCKET_SERVER, json.dumps(
            notification), headers=headers)
    except Exception:
        pass
    return True


class GenericFileUploadView(ModelViewSet):
    queryset = GenericFileUpload.objects.all()
    serializer_class = GenericFileUploadSerializer


class MessageView(ModelViewSet):
    queryset = Message.objects.select_related(
        "sender", "receiver").prefetch_related("message_attachments")
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticatedCustom,)

    def get_queryset(self):
        data = self.request.query_params.dict()
        user_id = data.get("user_id", None)

        if user_id:
            active_user_id = self.request.user.id
            return self.queryset.filter(Q(sender_id=user_id, receiver_id=active_user_id) | Q(sender_id=active_user_id, receiver_id=user_id)).distinct()
        return self.queryset

    def create(self, request, *args, **kwargs):
        try:
            request.data._mutable = True
        except:
            pass

        attachments = request.data.pop("attachments", None)

        if str(request.user.id) != str(request.data.get("sender_id", None)):
            raise Exception("Invalid request")

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if attachments:
            MessageAttachment.objects.bulk_create(
                [MessageAttachment(**attachment, message_id=serializer.data["id"]) for attachment in attachments])

            message_data = self.get_queryset().get(id=serializer.data["id"])
            return Response(self.serializer_class(message_data).data, status=201)

        handle_request(serializer)

        return Response(serializer.data, status=201)
