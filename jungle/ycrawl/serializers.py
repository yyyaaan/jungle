from select import select
from rest_framework import serializers

from .models import *
from commonlib.actions import perform_action


class VmActionSerializer(serializers.ModelSerializer):
    serializers.PrimaryKeyRelatedField(many=True, queryset=VmRegistry.objects.all())

    class Meta:
        model = VmActionLog
        fields = '__all__'

    def create(self, request):
        result_added = perform_action(request)
        return super().create(result_added) 


class VmSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmRegistry
        fields = '__all__'


class VmTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VmTrail
        fields = '__all__'

