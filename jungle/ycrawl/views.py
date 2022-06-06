
# Create your views here.
from rest_framework import viewsets, views, permissions, renderers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import render
from threading import Thread
from datetime import date


from ycrawl.models import *
from ycrawl.serializers import *
from ycrawl.ycrawlurl import YCrawlJobs, run_data_processor
from jungle.authentication import get_secret


class BatchJobListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Provide (read-only) list of batch jobs; 
    parse any value to completion to see full list
    All yCrawl Batch Job endpoints are listed here (sub routes)
    """
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
        
        YCrawlJobs().register_completion()
        records = BatchJobList.get_today_objects().filter(vmid=vmid, completion=False)
        output = "\n".join([x.nodejob for x in records])
        # VmTrail(vmid="self", event="nodejobs", info=f"{records.count()} returned").save()
        return render(request, "ycrawl/raw.html", {"output": output})

    @action(methods=['POST'], detail=False)
    def start(self, request, **kwargs):
        """start the daily job; role param is optional"""
        vmrole = request.data['role'] if 'role' in request.data else "crawler"
        vms = VmRegistry.objects.filter(role=vmrole)

        if len(vms):
            YCrawlJobs().register_jobs(force=('force' in request.data))
            event = "STOP" if 'stop' in request.data else "START"
            vmstartstop([x.vmid for x in vms], event, "Initated by API start-ycrawl")
        else:
            logger.info("No VM satisfies the given criteria.")

        return Response({"success": "ok", "ref": "http://yan.fi/ycrawl/actions"}, status=status.HTTP_202_ACCEPTED)

    @action(methods=['POST'], detail=False)
    def checkin(self, request, **kwargs):
        """check-in endpoint; no param expected; force offset (qutoed-int) will trigger data processing; reset"""
        if 'offset' in request.data:
            offset = int(request.data['offset'])
            if offset >= 0:
                VmTrail(vmid="self", event="Manual Data Processing", info=f"exceptional data processing with offset={offset}").save()
                thread = Thread(target=run_data_processor, args=[offset])
                thread.start()
                return Response({"data-processing": "started"}, status=status.HTTP_202_ACCEPTED)

        if 'reset' in request.data:
            YCrawlJobs().register_completion(deletion_detection=True)
            return Response({"register-completion": "reset all and rescanned for deleted files"}, status=status.HTTP_202_ACCEPTED)

        flag, res = YCrawlJobs().checkin()
        return Response({"success": res}, status=status.HTTP_202_ACCEPTED)


class VmActionLogViewSet(viewsets.ModelViewSet):
    """API endpoint for Vm Actions. POST will trigger actions. Decorate for notification"""
    queryset = VmActionLog.objects.filter(timestamp__date=date.today()).order_by("-timestamp")
    serializer_class = VmActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(methods=['POST'], detail=False)
    def notifydone(self, request, *args, **kwargs):
        """shortcut for crawler, vmid mandatory; a-no-shut-flag in config to override STOP action"""
        if YCrawlConfig.get_value("a-no-shutdown-flag") != date.today().strftime("%Y-%m-%d"):
            vmstartstop([request.data["vmid"]], "STOP", "notifydone endpoint")        
        YCrawlJobs().on_vm_completed()
        return Response(status=status.HTTP_201_CREATED)


class VmViewSet(viewsets.ModelViewSet):
    """VM Registry. Update in admin or via API."""
    queryset = VmRegistry.objects.all().order_by("vmid")
    serializer_class = VmSerializer
    permission_classes = [permissions.IsAuthenticated]


class VmTrailViewSet(viewsets.ModelViewSet):
    """API endpoint for VmTrail; entry is posted by VM directly"""
    queryset = VmTrail.objects.filter(timestamp__date=date.today()).order_by("-timestamp")
    serializer_class = VmTrailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class YCrawlConfigViewSet(viewsets.ModelViewSet):
    """yCrawl Configuration in simple tabular storage"""
    queryset = YCrawlConfig.objects.all().order_by("name")
    serializer_class = YCrawlConfigSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(methods=['GET'], detail=False)
    def worker(self, request, **kwargs):  
        """shortcut for workers to get setting"""      
        worker_settings = YCrawlConfig.get_json_by_name("worker-profile")
        return Response(worker_settings, status=status.HTTP_200_OK)
