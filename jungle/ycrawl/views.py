
# Create your views here.
from rest_framework import viewsets, permissions, renderers

from .models import *
from .serializers import *


API_RENDERERS = [renderers.AdminRenderer, renderers.BrowsableAPIRenderer, renderers.JSONRenderer, renderers.JSONOpenAPIRenderer]


class VmActionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Vm Actions. POST will trigger actions"""
    queryset = VmActionLog.objects.all().order_by("-timestamp")
    serializer_class = VmActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = API_RENDERERS


class VmViewSet(viewsets.ModelViewSet):
    """VM Registry. Update in admin or via API."""
    queryset = VmRegistry.objects.all().order_by("vmid")
    serializer_class = VmSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = API_RENDERERS

    def get_queryset(self):
        """optional filters"""        
        project = self.request.query_params.get("project", None)
        role = self.request.query_params.get("role", None)
        if project and role:
            return VmRegistry.objects.filter(project=project, role=role)
        if project:
            return VmRegistry.objects.filter(project=project)
        if role:
            return VmRegistry.objects.filter(role=role)

        return super().get_queryset()

class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail; entry is posted by VM directly"""
    queryset = VmTrail.objects.all().order_by("-timestamp")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = API_RENDERERS

