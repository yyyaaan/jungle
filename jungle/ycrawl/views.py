
# Create your views here.
from rest_framework import viewsets, permissions

from .models import *
from .serializers import *


class VmActionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Vm Actions, no auth required"""
    queryset = VmActionLog.objects.all().order_by("-timestamp")
    serializer_class = VmActionSerializer
    permission_classes = [permissions.IsAuthenticated]


class VmViewSet(viewsets.ModelViewSet):
    """API endpoint for VmRegistry"""
    queryset = VmRegistry.objects.all().order_by("vmid")
    serializer_class = VmSerializer
    permission_classes = [permissions.IsAuthenticated]


class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail, no auth required"""
    queryset = VmTrail.objects.all().order_by("-timestamp")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

