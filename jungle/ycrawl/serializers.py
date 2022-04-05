from json import loads, decoder
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, ValidationError

from .models import *
from commonlib.actions import perform_action


class VmActionSerializer(ModelSerializer):
    PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    class Meta:
        model = VmActionLog
        fields = '__all__'

    def create(self, request):
        result_added = perform_action(request)
        return super().create(result_added) 


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
