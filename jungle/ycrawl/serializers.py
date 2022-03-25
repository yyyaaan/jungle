from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import *

class VmSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VmRegistry
        fields = ["vmid", "project", "role", "provider", "zone", "resource", "batchnum"]


class VmTrailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VmTrail
        fields = ["vmid", "event", "timestamp", "info"]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']