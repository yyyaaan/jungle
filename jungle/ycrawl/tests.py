from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status

URL_VMS = "/ycrawl/vms/"
URL_TRAILS = "/ycrawl/trails/"
URL_ACTIONS = "/ycrawl/actions/"

class NoTokenAccessTests(TestCase):
    """No token, no auth'd user cases"""

    def setUp(self):
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
        self.vmdata = {"vmid":"testvm", "project":"a", "role": "a", "provider": "a", "zone": "a", "batchnum": 999}
        self.client = APIClient()
        # self.client.force_authenticate(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + Token.objects.create(user=self.user).key
        )

    """Test with Bearer Token, VmAction test in separate class"""
    def test_vm_registry_create_then_read(self):
        res = self.client.post(URL_VMS, self.vmdata)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.get(URL_VMS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual("testvm", res.data[0]['vmid'])

    def test_vm_action_read(self):
        res = self.client.get(URL_ACTIONS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_post_trail(self):
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


class VmGroupActionTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='unittest@yan.fi', password='unittestpassword', username='Unit Tester')
        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + Token.objects.create(user=self.user).key
        )

    def test_vm_action_create(self):
        """VM Action create and requested actions will be performed"""
        vm1 = {"vmid":"vm1", "project":"a", "role": "a", "provider": "a", "zone": "a", "batchnum": 999}
        vm2 = {"vmid":"vm2", "project":"a", "role": "a", "provider": "a", "zone": "a", "batchnum": 999}
        self.client.post(URL_VMS, vm1)
        self.client.post(URL_VMS, vm2)
         
        """vmids is register, confirm action logged"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["vm1", "vm2"], "event": "STOP"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        with open("jungle.log", "r") as f:
            last2log = " ".join(f.readlines()[-2:])
        self.assertIn("Action initiated: stop vm1", last2log)
        self.assertIn("Action initiated: stop vm2", last2log)

        """error if not a registered vm"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["unregistered"], "event": "error"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
