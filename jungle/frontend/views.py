from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.template import Template, Context
from django.conf import settings
from django.urls import URLPattern, URLResolver
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date
from logging import getLogger
from json import loads, dumps

from .models import *
from commonlib.vmmanager import vm_list_all
from ycrawl.serializers import *

# helper function (will be called be sitemap)
def make_sidenav():
    links = SiteUrl.objects.filter(menu2__lt=10000)
    menudata = {
        "dropgrp1": links.filter(menu2__lt=100).order_by("menu2"),
        "dropgrp2": links.filter(menu2__gt=100).order_by("menu2"),
    }

    t = open(f"{str(settings.BASE_DIR)}/templates/sidenavtemplate.html", "r").read()
    t = Template(t)
    x = t.render(Context(menudata))
    open(f"{str(settings.BASE_DIR)}/templates/sidenav.html", "w").write(x)
    
    return True


# Create your views here.
def hello(request):
    links = SiteUrl.objects.filter(menu1__lt=10000)
    pagedata = {
        "mainitems": links.filter(menu1__lt=100).order_by("menu1"),
        "dropgrp1": links.filter(menu1__gt=100, menu1__lt=200).order_by("menu1"),
        "dropgrp2": links.filter(menu1__gt=200).order_by("menu1"),
    }

    if "json" in request:
        return pagedata
    return render(request, 'frontend/index.html', pagedata)


@login_required(login_url='/admin/login/')
def get_urls(request):
    
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
    all_urls = [x for x in all_urls if "?P" not in x and "admin" not in x and "play" not in x]
    all_urls = set([x.replace("^", "").replace("$", "") for x in all_urls if len(x) > 1])

    prev_cnt = SiteUrl.objects.all().count()
    for one in sorted(all_urls):
        if SiteUrl.objects.filter(rawurl=one).count() == 0:
            item = SiteUrl(rawurl=one, cleanurl=one, menu1=123456, menu2=123456)
            item.save()


    pagedata = hello({"json": True})
    pagedata["extra"] = f"{SiteUrl.objects.all().count() - prev_cnt} new url."
    pagedata["allurls"] = all_urls
    pagedata["notlisted"] = SiteUrl.objects.filter(menu1__gt=1000)
    # read logs
    pagedata["log"] = open(f"{str(settings.BASE_DIR)}/jungle.log", "r").read()

    make_sidenav()

    return render(request, 'frontend/index.html', pagedata)






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




