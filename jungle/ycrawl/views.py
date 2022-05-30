
# Create your views here.
from rest_framework import viewsets, views, permissions, renderers, status
from rest_framework.response import Response
from rest_framework.decorators import action

from django.shortcuts import render
from datetime import date

from ycrawl.models import *
from ycrawl.serializers import *
from ycrawl.ycrawlurl import YCrawlJobs
from jungle.authentication import get_secret


class BatchJobListViewSet(viewsets.ReadOnlyModelViewSet):
    """Provide (read-only) list of batch jobs; parse any value to completion to see full list"""
    queryset = BatchJobList.get_today_objects()
    serializer_class = BatchJobListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vmid = self.request.query_params.get("vmid", None)
        completion = self.request.query_params.get("completion", False)

        res = BatchJobList.get_today_objects()
        if not completion:
            res = res.filter(completion=completion)
        if vmid:
            res = res.filter(vmid=vmid)
        return res

    @action(methods=['GET'], detail=False)
    def nodejobs(self, request, **kwargs):
        """Plain results for nodejs worker, vmid mandatory"""
        vmid = self.request.query_params.get("vmid", None) 
        if not vmid:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        
        records = BatchJobList.get_today_objects().filter(vmid=vmid, completion=False)
        output = "\n".join([x.nodejob for x in records])

        # create a trail
        VmTrail(vmid=vmid, event="GET joblist/nodejobs", info=f"{records.count()} returned").save()
        return render(request, "ycrawl/raw.html", {"output": output})


class VmActionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Vm Actions. POST will trigger actions. Decorate for notification"""
    queryset = VmActionLog.objects.all().order_by("-timestamp")
    serializer_class = VmActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['POST'], detail=False)
    def notifydone(self, request, *args, **kwargs):
        """Plain results for nodejs worker, vmid mandatory"""
        # shutdown the VM
        action_serializer = VmActionSerializer(data={
            "vmids": [request.data["VMID"]],
            "event": "STOP",
            "info": "notifydone endpoint", 
        })        
        if action_serializer.is_valid(raise_exception=True):
            action_serializer.save()
        
        # 
        YCrawlJobs().on_vm_completed(min_percentage=0.98)

        return Response(status=status.HTTP_201_CREATED)


class StartYcrawl(views.APIView):
    """Start yCrawl endpoints; register jobs and start vms"""
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self):
        self.vmrole = "crawler"
        self.isstart = True
    
    def start_ycrawl(self):
        vm_table = VmRegistry.objects.filter(role=self.vmrole)

        if len(vm_table):
            # register today's job; pk contronls non-dup
            YCrawlJobs().register_jobs()
            # start vms
            action_serializer = VmActionSerializer(data={
                "vmids": [x.vmid for x in vm_table],
                "event": ("START" if self.isstart else "STOP"),
                "info": "Initated by API start-ycrawl" 
            })        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()
            # add a trail
            VmTrail(
                vmid=", ".join([x.vmid.vmid for x in vm_table]), 
                event="Start yCrawl endpoint", 
                info=f"{vm_table.count()} called (IsStart={self.isstart})"
            ).save()
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
        return Response({"success": True, "vm_applied": vmids}, status=status.HTTP_202_ACCEPTED)


class VmViewSet(viewsets.ModelViewSet):
    """VM Registry. Update in admin or via API."""
    queryset = VmRegistry.objects.all().order_by("vmid")
    serializer_class = VmSerializer
    permission_classes = [permissions.IsAuthenticated]


class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail; entry is posted by VM directly"""
    queryset = VmTrail.objects.all().order_by("-timestamp")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class YCrawlConfigViewSet(viewsets.ModelViewSet):
    """yCrawl Configuration in simple tabular storage"""
    queryset = YCrawlConfig.objects.all().order_by("name")
    serializer_class = YCrawlConfigSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
