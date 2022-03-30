
# Create your views here.
from rest_framework import viewsets, views, permissions, renderers, status
from rest_framework.response import Response
from django.shortcuts import render

from .models import *
from .serializers import *


API_RENDERERS = [renderers.AdminRenderer, renderers.BrowsableAPIRenderer, renderers.JSONRenderer, renderers.JSONOpenAPIRenderer]

class StartYcrawl(views.APIView):
    """Start yCrawl endpoints"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        self.vmrole = "crawler"
    
    def start_ycrawl(self):
        vm_table = VmRegistry.objects.raw(f"select * from ycrawl_vmregistry where role='{self.vmrole}'")

        if len(vm_table):
            action_serializer = VmActionSerializer(data={
                "vmids": [x.vmid for x in vm_table],
                "event": "START",
                "info": "Initated by API start-ycrawl" 
            })        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()
        else:
            logger.info("No VM satisfies the given criteria.")

        return vm_table

    def get(self, request, format=None):
        self.vmrole = request.query_params['role'] if 'role' in request.query_params else "crawler"
        vm_table =  self.start_ycrawl()
        return render(request, "ycrawl/t1.html", {"h1text": "Action performed", "vm_table": vm_table})

    def post(self, request, format=None):
        self.vmrole = request.data['role'] if 'role' in request.data else "crawler"
        vmids = [x.vmid for x in self.start_ycrawl()]
        return Response({"sucess": True, "vm_applied": vmids}, status=status.HTTP_202_ACCEPTED)


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

