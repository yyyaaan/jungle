from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status


URL_VMS = "/ycrawl/vms/"
URL_TRAILS = "/ycrawl/trails/"

class NoTokenAccessTests(TestCase):
    """Craete a test user, but not auth/token, check if 401"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='unittest@yan.fi',
            password='unittestpassword',
            username='Unit Tester',
        )
        self.client = APIClient()

    def test_vm_registry_no_access(self):
        res = self.client.get(URL_VMS)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_trail_without_token(self):
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class BearerAccessTests(TestCase):
    """Create a test user, give him a token, test proper access"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='unittest@yan.fi',
            password='unittestpassword',
            username='Unit Tester',
        )

        self.client = APIClient()
        # self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + Token.objects.create(user=self.user).key
        )


    def test_vm_registry_access(self):
        """Test with Bearer, data cannot be compared because it is a test"""
        res = self.client.get(URL_VMS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_post_trail(self):
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

