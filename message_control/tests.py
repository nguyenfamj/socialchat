import json
from rest_framework.test import APITestCase
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from six import BytesIO
from PIL import Image

# Create your tests here.


def create_image(storage, filename, size=(100, 100), image_mode='RGB', image_format='PNG'):
    data = BytesIO()
    Image.new(image_mode, size).save(data, image_format)
    data.seek(0)

    if not storage:
        return data

    image_file = ContentFile(data.read())
    return storage.save(filename, image_file)


class TestFileUpload(APITestCase):
    file_upload_url = '/message/file-upload'

    def test_file_upload(self):
        avatar = create_image(None, 'avatar.png')
        avatar_file = SimpleUploadedFile('avatar1.png', avatar.getvalue())
        data = {
            "file_upload": avatar_file
        }

        # POST
        response = self.client.post(self.file_upload_url, data=data)
        result = response.json()

        # Check for the return value
        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["id"], 1)


class TestMessage(APITestCase):
    message_url = "/message/message"
    file_upload_url = '/message/file-upload'
    login_url = "/user/login"

    def setUp(self):
        from user_control.models import CustomUser, UserProfile

        payload = {
            "username": "UserA",
            "password": "UserApassword",
            "email": "UserAemail@gmail.com",
        }

        # Create user A
        self.sender = CustomUser.objects.create_user(**payload)
        UserProfile.objects.create(
            first_name="User", last_name="A", user=self.sender, caption="Sender", about="I am the sender")

        # Login user A
        response = self.client.post(self.login_url, data=payload)
        result = response.json()

        self.bearer = {
            "HTTP_AUTHORIZATION": "Bearer {}".format(result["access"])
        }

        # Create user B
        self.receiver = CustomUser.objects.create_user(
            username="UserB", password="userBpassword", email="UserBemail@gmail.com")
        UserProfile.objects.create(first_name="User", last_name="B",
                                   user=self.receiver, caption="Receiver", about="I am the receiver")

    def test_post_message(self):

        avatar = create_image(None, 'avatar.png')
        avatar_file = SimpleUploadedFile('avatar1.png', avatar.getvalue())
        data = {
            "file_upload": avatar_file
        }
        response = self.client.post(
            self.file_upload_url, data=data, **self.bearer)
        file_content = response.json()["id"]

        payload = {
            "sender_id": self.sender.id,
            "receiver_id": self.receiver.id,
            "message": "Hi, I am user A",
            "attachments": [
                {"caption": "new image",
                 "attachment_id": file_content
                 }, {
                    "attachment_id": file_content
                }
            ]
        }

        # Post message
        response = self.client.post(self.message_url, data=json.dumps(
            payload), content_type="application/json", **self.bearer)
        result = response.json()
        print(result)

        # Check all tests passed
        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["message"], "Hi, I am user A")
        self.assertEqual(result["sender"]["user"]["username"], "UserA")
        self.assertEqual(result["receiver"]["user"]["username"], "UserB")
        self.assertEqual(result["message_attachments"]
                         [0]["attachment"]["id"], 1)
        self.assertEqual(result["message_attachments"]
                         [0]["caption"], "new image")

    def test_update_message(self):
        new_message = {
            "sender_id": self.sender.id,
            "receiver_id": self.receiver.id,
            "message": "Hello, this is the new message"
        }
        self.client.post(self.message_url, data=new_message, **self.bearer)

        # Update message
        updated_message = {
            "message": "Hello, this is the new updated message",
            "is_read": True
        }
        response = self.client.patch(
            self.message_url+"/1", data=updated_message, **self.bearer)

        result = response.json()

        # Check all tests passed
        self.assertEqual(response.status_code, 200)
