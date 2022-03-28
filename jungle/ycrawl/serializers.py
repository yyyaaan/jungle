from turtle import forward
from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import *


def perform_action(action, vmid_list):
    print(f"Forwarding {action} with parameters {vmid_list}")


class VmActionSerializer(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    def create(self, request):
        perform_action(
            action = request["event"],
            vmid_list = [x.vmid for x in request["vmids"]]
        )
        return super(VmActionSerializer, self).create(request)

    class Meta:
        model = VmActionLog
        fields = ["vmids", "event", "info", "timestamp"]



class VmSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmRegistry
        fields = ["vmid", "project", "role", "provider", "zone", "resource", "batchnum"]


class VmTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmTrail
        fields = ["vmid", "event", "timestamp", "info"]

