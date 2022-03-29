from rest_framework import serializers

from .models import *


def perform_action(validated_request):
    # startup, shutdown based on vmid_list
    # logger.info("Action received from VM Action Serializer")
    action = validated_request["event"]
    vmid_list = [x.vmid for x in validated_request["vmids"]]

    if action == "START":
        for vmid in vmid_list:
            logger.info(f"Action initiated: start {vmid}")
        return True 

    if action == "STOP":
        for vmid in vmid_list:
            logger.info(f"Action initiated: stop {vmid}")
        return True

    logger.warn(f"Unknown action")
    return False



class VmActionSerializer(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    def create(self, request):
        perform_action(request)
        return super().create(request) 

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

