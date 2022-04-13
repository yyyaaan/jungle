from django_extensions.management.jobs import HourlyJob
from datetime import datetime


from ycrawl.views import *

class Job(HourlyJob):

    def execute(self):
        utchour = datetime.utcnow().hour
        threshold = YCrawlConfig.get_json_by_name("general")["retry-threshold"]
        print(f"current time is {utchour}hr, retry threshold is {threshold}")

        # n_vms should -1 since "all" is there 
        urls, batchref = GetNodeJobs().get(request={}, format="CRON")
        batchref.pop("all")

        to_run_vmids = []
        for one_vm in batchref:
            jobs = [x for x in urls if (int(x.split(" ")[2][-4:]) % len(batchref) == batchref[one_vm])]
            if len(jobs) > threshold:
                to_run_vmids.append(one_vm)

        # start vms if necessary (already started cases is handled in seriliazer)
        if len(to_run_vmids):
            action_serializer = VmActionSerializer(data={
                "vmids": to_run_vmids,
                "event": "STOP",
                "info": "check-in cron jobs"
            })        
            if action_serializer.is_valid(raise_exception=True):
                action_serializer.save()
            else:
                logger.info(f"check-in failed when starting VMs")

