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
