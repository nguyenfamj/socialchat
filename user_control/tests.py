from rest_framework.test import APITestCase

from message_control.tests import create_image, SimpleUploadedFile
from .views import get_random, get_access_token, get_refresh_token
from .models import CustomUser, UserProfile

# Create your tests here.


class TestUniversalFunction(APITestCase):
    def test_get_random(self):

        rand1 = get_random(10)
        rand2 = get_random(20)
        rand3 = get_random(20)

        # Check for result generated
        self.assertTrue(rand1)

        # Check for different between rand1 and rand2
        self.assertNotEqual(rand1, rand2)

        # Check the length is correct
        self.assertEqual(len(rand1), 10)
        self.assertEqual(len(rand3), 20)

    def test_get_access_token(self):
        payload = {"user_id": 20}

        token = get_access_token(payload)

        # Check if the result is returned
        self.assertTrue(token)

    def test_get_refresh_token(self):

        token = get_refresh_token()

        # Check if the result is returned
        self.assertTrue(token)


class TestAuthentication(APITestCase):
    login_url = "/user/login"
    register_url = "/user/register"
    refresh_url = "/user/refresh"

    def test_register(self):
        payload = {
            "username": "nguyenfamj1",
            "password": "newPassword123",
            "email": "nguyenfamj1409@gmail.com"
        }

        response = self.client.post(self.register_url, data=payload)

        # Check status code 201
        self.assertEqual(response.status_code, 201)

    def test_login(self):
        payload = {
            "username": "nguyenfamj1",
            "password": "newPassword123",
            "email": "nguyenfamj1409@gmail.com"
        }

        # First register user
        self.client.post(self.register_url, data=payload)

        # Login user
        response = self.client.post(self.login_url, data=payload)
        result = response.json()

        self.assertEqual(response.status_code, 200)

        # Check for access token and refresh token
        self.assertTrue(result["access"])
        self.assertTrue(result["refresh"])

    def test_refresh(self):
        payload = {
            "username": "nguyenfamj1",
            "password": "newPassword123",
            "email": "nguyenfamj1409@gmail.com"
        }

        # First register user
        self.client.post(self.register_url, data=payload)

        # Login user
        response = self.client.post(self.login_url, data=payload)
        refresh = response.json()["refresh"]

        # Get refresh token
        response = self.client.post(
            self.refresh_url, data={"refresh": refresh})
        result = response.json()

        # Check status code 200
        self.assertEqual(response.status_code, 200)

        # Check for access token and refresh token
        self.assertTrue(result["access"])
        self.assertTrue(result["refresh"])


class TestUserInfo(APITestCase):
    profile_url = "/user/profile"
    login_url = "/user/login"
    file_upload_url = "/message/file-upload"

    def setUp(self):
        payload = {
            "username": "nguyenfamj1",
            "password": "newPassword123",
            "email": "nguyenfamj1409@gmail.com"
        }
        self.user = CustomUser.objects.create_user(**payload)

        # Login
        response = self.client.post(self.login_url, data=payload)
        result = response.json()

        self.bearer = {
            "HTTP_AUTHORIZATION": "Bearer {}".format(result["access"])
        }

    def test_post_user_profile(self):

        payload = {
            "user_id": self.user.id,
            "first_name": "Nguyen",
            "last_name": "Pham",
            "caption": "Study, study more, study forever",
            "about": "Full stack developer"
        }
        response = self.client.post(
            self.profile_url, data=payload, **self.bearer)
        result = response.json()

        # Test
        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["first_name"], "Nguyen")
        self.assertEqual(result["last_name"], "Pham")
        self.assertEqual(result["user"]["username"], "nguyenfamj1")

    def test_post_user_profile_with_profile_picture(self):

        avatar = create_image(None, 'avatar.png')
        avatar_file = SimpleUploadedFile('avatar.png', avatar.getvalue())
        data = {
            "file_upload": avatar_file
        }

        response = self.client.post(self.file_upload_url, data, **self.bearer)
        result = response.json()

        payload = {
            "user_id": self.user.id,
            "first_name": "Nguyen",
            "last_name": "Pham",
            "caption": "Study, study more, study forever",
            "about": "Full stack developer",
            "profile_picture_id": result["id"]
        }

        response = self.client.post(
            self.profile_url, data=payload, **self.bearer)
        result = response.json()

    def test_update_user_profile(self):

        payload = {
            "user_id": self.user.id,
            "first_name": "Nguyen",
            "last_name": "Pham",
            "caption": "Study, study more, study forever",
            "about": "Full stack developer",
        }

        response = self.client.post(
            self.profile_url, data=payload, **self.bearer)
        result = response.json()

        # Update profile
        updated_payload = {
            "first_name": "Cristiano",
            "last_name": "Ronaldo",
        }

        response = self.client.patch(
            self.profile_url + f"/{result['id']}", data=updated_payload, **self.bearer)
        result = response.json()

        # Test check result
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["first_name"], "Cristiano")
        self.assertEqual(result["last_name"], "Ronaldo")
        self.assertEqual(result["user"]["username"], "nguyenfamj1")

    def test_search_user(self):

        UserProfile.objects.create(
            user=self.user, first_name="Nguyen", last_name="Pham", caption="This is the caption for this account", about="Full-stack developer")

        user2 = CustomUser.objects.create_user(
            username="user2", password="user2password", email="user2@gmail.com")
        UserProfile.objects.create(
            user=user2, first_name="User2", last_name="Hopkins", caption="This is the caption for this account", about="Full-stack developer")

        user3 = CustomUser.objects.create_user(
            username="user3", password="user3password", email="user3@gmail.com")
        UserProfile.objects.create(
            user=user3, first_name="User3", last_name="Stone", caption="This is the caption for this account", about="Full-stack developer")

        # Keyword = nguyen pham
        url = self.profile_url + "?keyword=nguyen pham"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]
        print(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)

        # Keyword = user2
        url = self.profile_url + "?keyword=user2"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]
        print(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user"]["username"], "user2")
        self.assertEqual(result[0]["unseen"], 0)

        # Keyword = user3
        url = self.profile_url + "?keyword=user3"

        response = self.client.get(url, **self.bearer)
        result = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user"]["username"], "user3")
