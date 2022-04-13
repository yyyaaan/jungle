from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.conf import settings
from django.urls import URLPattern, URLResolver
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date
from logging import getLogger
from json import loads, dumps

from commonlib.vmmanager import vm_list_all
from ycrawl.serializers import *

logger = getLogger("frontend")

# Create your views here.
def hello(request):

    urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])
    def list_urls(lis, acc=None):
        if acc is None:
            acc = []
        if not lis:
            return
        l = lis[0]
        if isinstance(l, URLPattern):
            yield acc + [str(l.pattern)]
        elif isinstance(l, URLResolver):
            yield from list_urls(l.url_patterns, acc + [str(l.pattern)])
        yield from list_urls(lis[1:], acc)

    all_urls = [''.join(p) for p in list_urls(urlconf.urlpatterns)]
    tmp = "<br/>".join([x for x in all_urls if "admin" not in x])

    return render(request, 'frontend/index.html', {"h1text": "Hello Frontend", "mainhtml": tmp})


def show_ycrawl_config(request):

    all_configs = [
        f"<h2>Configuration: <a href='/admin/ycrawl/ycrawlconfig/{x.name}/change/'>{x.name}</a></h2>" +
        f"<pre>{dumps(loads(x.value), indent=4)}</pre>"
        for x in YCrawlConfig.objects.order_by("name").all()
    ]

    payload = {
        "mainhtml": f"""
            <div>{"</div><div>".join(all_configs)}</div>
            <p><a target='_blank' href='/admin/ycrawl/vmactionlog/'> Action Log</a> | 
               <a target='_blank' href='/admin/ycrawl/vmtrail/'> Trails </a></p>    
        """
    }

    return render(request, 'frontend/index.html', payload)

@login_required(login_url='/admin/login/')
def vm_management(request):
    if request.method != "GET":
        return HttpResponseForbidden

    if "status" in request.GET:
        n_running, vms = vm_list_all()
        # add red color for running status
        for entry in vms:
            txt = entry["header"].split(" ")
            if txt[1].upper() not in ("TERMINATED", "STOPPED", "VMDEALLOCATED", "SHELVED_OFFLOADED"):
                txt[1] = " <b style='color:salmon'>" + txt[1] + "</b> "
            entry["header"] = " ".join(txt)
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
    nice_br = "<br/>" #<span style='color:transparent'>00:00:00 </span>"
    logs = [
        f"""
        === {x.timestamp.strftime('%H:%M:%S')} {x.event}
        <i>{','.join([xx.vmid for xx in x.vmids.all()])}</i> ===
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
            <p>{"</p><p>".join(logs)}</p>
            <p>{"</p><p>".join(trails)}</p>
            <p>
                <a target='_blank' href='/admin/ycrawl/vmactionlog/'> Action Log</a> | 
                <a target='_blank' href='/admin/ycrawl/vmtrail/'> Trails </a>
            </p>    
        """
    }

    return render(request, 'minimal.html', payload)
