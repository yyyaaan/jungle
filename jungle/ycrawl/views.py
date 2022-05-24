
# Create your views here.
from rest_framework import viewsets, views, permissions, renderers, status
from rest_framework.response import Response
from django.shortcuts import render
from datetime import date

from .models import *
from .serializers import *
from commonlib.ycrawlurlmaker import call_url_coordinator
from commonlib.secretmanager import get_secret


API_RENDERERS = [renderers.AdminRenderer, renderers.BrowsableAPIRenderer, renderers.JSONRenderer, renderers.JSONOpenAPIRenderer]

class RunData(views.APIView):
    """Call for data processor to run/stop (backward compatible actions)"""
    #permission_classes = [permissions.AllowAny]

    def post(self, request):
        if "AUTH" not in request.data or request.data["AUTH"] != get_secret("ycrawl-simple-auth"):
            return Response({"success": False}, status=status.HTTP_403_FORBIDDEN)

        try:
            action_serializer = VmActionSerializer(data={
                "vmids": [request.data['VMID']],
                "event": ("STOP" if "STOP" in request.data else "START"),
                "info": "called from rundata endpoints" 
            })        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()

            return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(str(e))
            return Response({"success": False}, status=status.HTTP_503_SERVICE_UNAVAILABLE)



class GetNodeJobs(views.APIView):
    """Provide list of NodeJS jobs for yCrawl nodes"""

    def __init__(self):
        self.debug = True
        # get total batches based on started VMs
        qualified_log = VmActionLog.objects.filter(
            info__icontains = "API start-ycrawl",
            timestamp__gte = date.today(),
        )
        if not self.debug:
            qualified_log.filter(event="START")

        working_vms = qualified_log.last().vmids.all() if len(qualified_log) else VmRegistry.objects.filter(role="crawler")
        self.batchref = dict([(x.vmid, x.batchnum) for x in working_vms])
        self.batchref["all"] = 999
        
    def get(self, request, format=None):
        if format=="CRON": 
            return call_url_coordinator(no_check=self.debug, type="LIST"), self.batchref

        if 'vmid' not in request.query_params or request.query_params["vmid"] not in self.batchref:
            return Response({"message": "invalid vmid"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        batchn = self.batchref[request.query_params["vmid"]]
        output = call_url_coordinator(
            batch = batchn,
            total_batches = len(self.batchref),
            no_check = self.debug,
            type = "ONE"
        )

        n_output = len(output.split('\n'))
        trail_serializer = VmTrailSerializer(data={
            "vmid": request.query_params["vmid"],
            "event": "NodeJS jobs requested",
            "info": f"{n_output} jobs returned for batch-{batchn}" 
        })        
        if trail_serializer.is_valid(raise_exception=True):
            trail_serializer.save()

        return render(request, "ycrawl/raw.html", {"output": output})


class StartYcrawl(views.APIView):
    """Start yCrawl endpoints"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        self.vmrole = "crawler"
        self.isstart = True
    
    def start_ycrawl(self):
        vm_table = VmRegistry.objects.raw(f"select * from ycrawl_vmregistry where role='{self.vmrole}'")

        if len(vm_table):
            action_serializer = VmActionSerializer(data={
                "vmids": [x.vmid for x in vm_table],
                "event": ("START" if self.isstart else "STOP"),
                "info": "Initated by API start-ycrawl" 
            })        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()
        else:
            logger.info("No VM satisfies the given criteria.")

        return vm_table
    
    def get(self, request, format=None):
        self.vmrole = request.query_params['role'] if 'role' in request.query_params else "crawler"
        self.isstart = False if 'stop' in request.query_params else True
        vm_table =  self.start_ycrawl()
        return render(request, "ycrawl/t1.html", {"h1text": "Action performed", "vm_table": vm_table})

    def post(self, request, format=None):
        self.vmrole = request.data['role'] if 'role' in request.data else "crawler"
        self.isstart = False if 'stop' in request.data else True
        vmids = [x.vmid for x in self.start_ycrawl()]
        if format=="CRON": return "OK"
        return Response({"success": True, "vm_applied": vmids}, status=status.HTTP_202_ACCEPTED)


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


class VmActionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Vm Actions. POST will trigger actions"""
    queryset = VmActionLog.objects.all().order_by("-timestamp")
    serializer_class = VmActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = API_RENDERERS


class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail; entry is posted by VM directly"""
    queryset = VmTrail.objects.all().order_by("-timestamp")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = API_RENDERERS


class YCrawlConfigViewSet(viewsets.ModelViewSet):
    """yCrawl Configuration in simple tabular storage"""
    queryset = YCrawlConfig.objects.all().order_by("name")
    serializer_class = YCrawlConfigSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    renderer_classes = API_RENDERERS
