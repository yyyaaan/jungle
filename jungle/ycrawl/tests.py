from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status

from .models import *

URL_VMS = "/ycrawl/vms/"
URL_TRAILS = "/ycrawl/trails/"
URL_ACTIONS = "/ycrawl/actions/"
URL_START = "/ycrawl/joblist/start/"

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

    def test_vm_action_without_token(self):
        """yCrawl START cannot be called without token"""
        res = self.client.get(URL_START)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        res = self.client.post(URL_START)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_trail_without_token(self):
        """NOT ok to post a VM trail"""
        res = self.client.post(URL_TRAILS, data={"vmid": "test", "event":"test"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_trail_without_token(self):
        """VM trail is viewable to all"""
        res = self.client.get(URL_TRAILS)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class BearerAccessTests(TestCase):
    """Create a test user, give him a token, test proper access"""

    def setUp(self):
        self.user = User.objects.create_user(email='unittest@yan.fi', password='unittestpassword', username='Unit Tester')
        self.vmdata = {"vmid":"testvm", "project":"a", "role": "a", "provider": "a", "zone": "a", "batchnum": 999}
        self.client = APIClient()
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


class VmActionNShortcutTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='unittest@yan.fi', password='unittestpassword', username='Unit Tester')
        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + Token.objects.create(user=self.user).key
        )
        # load some vms
        vm1 = {"vmid":"testvm1", "project":"a", "role": "b", "provider": "c", "zone": "a", "batchnum": 999}
        vm2 = {"vmid":"testvm2", "project":"a", "role": "b", "provider": "c", "zone": "a", "batchnum": 999}
        self.client.post(URL_VMS, vm1)
        self.client.post(URL_VMS, vm2)

    def test_vm_action_unregistered(self):
        """action gives error if not a registered vm"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["unregistered"], "event": "error"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vm_action_create(self):         
        """vmids is register, db should record also result"""
        res = self.client.post(URL_ACTIONS, data={"vmids":["testvm1", "testvm2"], "event": "STOP"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VmActionLog.objects.all().count(), 1)
        self.assertIn("testvm1 passed", VmActionLog.objects.all().last().result)
        self.assertIn("testvm2 passed", VmActionLog.objects.all().last().result)
        
    def test_start_ycrawl(self):
        """Using shortcut should also call action to perform, and result is passed"""
        prev_count = VmActionLog.objects.all().count()
        res = self.client.post(URL_START, data={"role": "b"})
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        # actionlog is also created
        self.assertEqual(VmActionLog.objects.all().count() - prev_count, 1)
        self.assertIn("testvm1 passed", VmActionLog.objects.all().last().result)
        self.assertIn("testvm2 passed", VmActionLog.objects.all().last().result)






