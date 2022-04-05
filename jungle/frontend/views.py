from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date
from logging import getLogger

from commonlib.vmmanager import vm_list_all
from commonlib.ycrawlurlmaker import call_url_coordinator

from ycrawl.serializers import *

logger = getLogger("frontend")

# Create your views here.
def hello(request):
    tmp = call_url_coordinator(batch=999, total_batches=1, no_check=True, type="ARR")
    return render(request, 'frontend/index.html', {"h1text": "Hello Frontend", "mainhtml": len(tmp)})


@login_required(login_url='/admin/login/')
def vm_management(request):
    if request.method != "GET":
        return HttpResponseForbidden

    if "status" in request.GET:
        n_running, vms = vm_list_all()
    else:
        n_running, vms = -1, VmRegistry.objects.raw("""
            select  vmid || "  [" || project || " - " || role || "]" as header,
                    "<a href='/vms?status=1'>click to load status</a>" as content,
                    case when project = "yCrawl" then "loyalty" else "filter_drama" end as icon,
                    vmid
            from ycrawl_vmregistry 
            where role != "test"
        """)

    info = f"{n_running} active computing nodes" if n_running > 0 else ""
    
    return render(request, 'frontend/vmlist.html', {"debug_text": info, "vm_table": vms})


@login_required(login_url='/admin/login/')
def vm_action(request):
    if request.method != "POST":
        return HttpResponseForbidden()
    
    """Peform Action using Serializer"""
    action_serializer = VmActionSerializer(data={
        "vmids": [request.POST.get("VMID")],
        "event": request.POST.get("ACTION"),
        "info": f"Frontend action by user [{request.user.username}]" 
    })        
    if action_serializer.is_valid(raise_exception=True):
        action_serializer.save()
    else:
        logger.info(f"Frontend VM Action failed for [{request.user.username}]")
        return HttpResponseBadRequest()

    """Get some data"""
    nice_br = "<br/><span style='color:transparent'>00:00:00 </span>"
    logs = [
        f"""
        {x.timestamp.strftime('%H:%M:%S')} {x.event}
        <i>{','.join([xx.vmid for xx in x.vmids.all()])}</i>
        {nice_br} {x.result}
        {nice_br} {x.info}
        """ for x in VmActionLog.objects.filter(timestamp__gte=date.today()).order_by("-timestamp")[:10]
    ]
    trails = [
        f"{x.timestamp.strftime('%H:%M:%S')} {x.event} {x.vmid} {nice_br} {x.info}" 
        for x in VmTrail.objects.filter(timestamp__gte=date.today()).order_by("-timestamp")[:10]
    ]

    payload = {
        "h1text": "VM Action Submitted",
        "mainhtml": f"""
            <p>Below are abstract of Today's latest 10 activity log.</p>
            <p>{"<br/>".join(logs)}</p>
            <p>{"<br/>".join(trails)}</p>
            <p>
                <a target='_blank' href='/admin/ycrawl/vmactionlog/'> Action Log</a> | 
                <a target='_blank' href='/admin/ycrawl/vmtrail/'> Trails </a>
            </p>    
        """
    }

    return render(request, 'frontend/minimal.html', payload)
