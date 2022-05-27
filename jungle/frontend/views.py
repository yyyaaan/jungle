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
from .scripts import *
from ycrawl.serializers import *


# helper function (will be called be sitemap)
def make_sidenav():
    """write sidenav to static html; other pages will load that"""
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
    lists = SiteUrl.objects.filter(menu3__lt=10000)
    pagedata = {
        "mainitems": links.filter(menu1__lt=100).order_by("menu1"),
        "dropgrp1": links.filter(menu1__gt=100, menu1__lt=200).order_by("menu1"),
        "dropgrp2": links.filter(menu1__gt=200).order_by("menu1"),
        "listgrp1": lists.filter(menu3__gt=1000, menu3__lt=2000).order_by("menu3"),
        "listgrp3": lists.filter(menu3__gt=3000, menu3__lt=4000).order_by("menu3"),
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
            item = SiteUrl(rawurl=one, cleanurl=f"/{one}", menu1=123456, menu2=123456, menu3=123456)
            item.save()


    pagedata = hello({"json": True})
    pagedata["extra"] = f"{SiteUrl.objects.all().count() - prev_cnt} new url."
    pagedata["allurls"] = all_urls # when rendering, prefix a backslash!!!
    pagedata["notlisted"] = SiteUrl.objects.filter(menu1__gt=10000, menu2__gt=10000, menu3__gt=10000).exclude(menu1=1000000)
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



def job_overview(request):

    GSBUCKET, RUN_MODE, _ = meta_major()

    info, n_all, n_todo, n_done, n_forfeit, n_error, nu_error =  call_url_coordinator(type="INFO")
    all_files, info_str = storage_file_viewer()

    pagedata=dict(
        completed_percent = f"{(1-n_todo/n_all):.2%}",
        n_jobs = f"{n_all-n_todo}/{n_all}",
        jobs_detail = f"{n_done} completed<br/>{nu_error}({n_error})+{n_forfeit} issues",
        jobs_str = info,
        info_str = f"  {info_str}",
        all_files = all_files,
        gss_link = f"https://console.cloud.google.com/storage/browser/{GSBUCKET}/{RUN_MODE}/{datetime.now().strftime('%Y%m/%d')}",
        gso_link = f"https://console.cloud.google.com/storage/browser/yyyaaannn-us/yCrawl_Output/{datetime.now().strftime('%Y%m')}",
    )

    return render(request, 'frontend/overview.html', pagedata)


@login_required(login_url='/admin/login/')
def job_overview_log(request):
    return render(request, "frontend/overviewlog.html", {"logs_by_vm": get_simple_log()})


def job_overview_vmplot(request):
    _, vm_list = vm_list_all()
    pagedata = {"graphJSON": get_geoplot_json(
        vms=vm_list, 
        height=int(0.5 * int(request.GET["width"])), 
        width=int(request.GET["width"])
    )}
    return render(request, 'frontend/overviewvmplot.html', pagedata)

