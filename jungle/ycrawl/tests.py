from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status


URL_VMS = "/ycrawl/vms/"
URL_TRAILS = "/ycrawl/trails/"
URL_ACTIONS = "/ycrawl/actions/"

class NoTokenAccessTests(TestCase):
    """Craete a test user, but not auth/token"""

    def setUp(self):
        self.user = User.objects.create_user(email='unittest@yan.fi', password='unittestpassword', username='Unit Tester')
        self.client = APIClient()

    def test_vm_registry_without_token(self):
        res = self.client.get(URL_VMS)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vm_action_without_token(self):
        res = self.client.get(URL_ACTIONS)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_trail_without_token(self):
        """NOT ok to post, but ok to get"""
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_trail_without_token(self):
        res = self.client.get(URL_TRAILS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class BearerAccessTests(TestCase):
    """Create a test user, give him a token, test proper access"""

    def setUp(self):
        self.user = User.objects.create_user(email='unittest@yan.fi', password='unittestpassword', username='Unit Tester')
        self.vmdata = data={"vmid":"testvm", "project":"a", "role": "a", "provider": "a", "zone": "a", "batchnum": 999}
        self.client = APIClient()
        # self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + Token.objects.create(user=self.user).key
        )

    """Test with Bearer Token"""
    def test_vm_registry_create_then_read(self):
        
        res = self.client.post(URL_VMS, self.vmdata)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.get(URL_VMS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual("testvm", res.data[0]['vmid'])

    def test_vm_action_read(self):
        res = self.client.get(URL_ACTIONS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_vm_action_create(self):
        self.client.post(URL_VMS, self.vmdata)
        """vmids is a list containing registered vm"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["testvm"], "event": "OK"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        """error if not a registered vm"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["unregistered"], "event": "error"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_trail(self):
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

