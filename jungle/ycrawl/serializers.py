from select import select
from rest_framework import serializers

from .models import *
from .actions import perform_action


class VmActionShortcutSerializer(serializers.ModelSerializer):
    """Will get a correct list of vms to send to VmActionSerializer"""
    class Meta:
        model = VmActionShortcut
        fields = '__all__'

    def create(self, request):
        normal_create = super().create(request)

        # get the group of VMs
        selected_vms = VmRegistry.objects.exclude(project = "test")
        print(len(selected_vms))
        if "project" in request and len(request["project"]) > 1:
            selected_vms = selected_vms.filter(project = request.pop("project"))
            print(len(selected_vms))
        if "role" in request and len(request["role"]) > 1:
            selected_vms = selected_vms.filter(role = request.pop("role"))
            print(len(selected_vms))
        if "provider" in request and len(request["provider"]) > 1 :
            selected_vms = selected_vms.filter(provider = request.pop("provider"))
            print(len(selected_vms))

        # forward to VmActionSerializer to perform the action
        if len(selected_vms):
            request["vmids"] = [x.vmid for x in selected_vms]
            request["info"] = "Forwarded by Shortcut. " + (request["info"] if "info" in request else "")
            action_serializer = VmActionSerializer(data=request)        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()
        else:
            logger.info("Shortcut does not find any VM.")

        return normal_create


class VmActionSerializer(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    class Meta:
        model = VmActionLog
        fields = '__all__'

    def create(self, request):
        perform_action(request)
        return super().create(request) 



class VmSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmRegistry
        fields = '__all__'


class VmTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmTrail
        fields = '__all__'

