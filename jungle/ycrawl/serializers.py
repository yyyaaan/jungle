from json import loads, decoder
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ValidationError

from ycrawl.models import *
from ycrawl.vmmanager import *



class VmActionSerializer(ModelSerializer):
    PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    class Meta:
        model = VmActionLog
        fields = '__all__'

    def create(self, request):
        validated_request = request
        results = ["**"]
        try:
            action = validated_request["event"]
            vmid_list = [x.vmid for x in validated_request["vmids"]]

            if action == "START":
                for vmid in vmid_list:
                    _, info = vm_startup(vmid)
                    results.append(info)            
            elif action == "STOP":
                for vmid in vmid_list:
                    _, info = vm_shutdown(vmid)
                    results.append(info)
            else:
                logger.warn(f"Unknown action {action}")
                results.append(f"Unkonw action")
        except Exception as e:
            logger.error(f"Error in performing action: {str(e)}")
            results.append(f"Error occured: {str(e)}")

        validated_request['result'] = "; ".join(results)
        return super().create(validated_request) 


class VmSerializer(ModelSerializer):
    class Meta:
        model = VmRegistry
        fields = '__all__'


class VmTrailSerializer(ModelSerializer):
    class Meta:
        model = VmTrail
        fields = '__all__'


class YCrawlConfigSerializer(ModelSerializer):
    class Meta:
        model = YCrawlConfig
        fields = '__all__'


class BatchJobListSerializer(ModelSerializer):
    class Meta:
        model = BatchJobList
        fields = '__all__'


def vmstartstop(vmids, event, info):
    """Shorthanded action serailized"""
    action_serializer = VmActionSerializer(data={
        "vmids": ([vmids] if type(vmids) == str else vmids),
        "event": event,
        "info": info, 
    })        
    if action_serializer.is_valid(raise_exception=True):
        action_serializer.save()

    return True