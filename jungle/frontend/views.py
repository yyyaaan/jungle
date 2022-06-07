from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.template import Template, Context
from django.conf import settings
from django.urls import URLPattern, URLResolver
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from json import loads, dumps
from plotly.utils import PlotlyJSONEncoder
import plotly.express as px

from frontend.models import *
from ycrawl.models import *
from ycrawl.vmmanager import vm_list_all
from jungle.settings import BASE_DIR, MEDIA_ROOT


# helper function (will be called be sitemap)
def make_sidenav():
    """write sidenav to static html; other pages will load that"""
    links = SiteUrl.objects.filter(menu2__lt=10000)
    menudata = {
        "dropgrp1": links.filter(menu2__lt=100).order_by("menu2"),
        "dropgrp2": links.filter(menu2__gt=100).order_by("menu2"),
    }

    t = open(f"{str(BASE_DIR)}/templates/sidenavtemplate.html", "r").read()
    t = Template(t)
    x = t.render(Context(menudata))
    open(f"{str(BASE_DIR)}/templates/sidenav.html", "w").write(x)
    
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
    pagedata["ypoints"] = SiteUrl.objects.filter(cleanurl__icontains="ycrawl")
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

    gsbucket, runmode = YCrawlConfig.get_value("bucket"), YCrawlConfig.get_value("scope")
    # no longer update completion status from gs; expect updated already.
    
    jobs = BatchJobList.get_today_objects()
    n_all, n_todo = jobs.count(), jobs.filter(completion=False).count() 
    n_forfeit = jobs.filter(note__startswith="X").count()
    n_error = jobs.filter(note__endswith="E").exclude(note__startswith="X").count()
    n_ok = jobs.filter(completion=True).exclude(note__startswith="X").count()

    try:
        with open(f"{MEDIA_ROOT}cache/{date.today().strftime('%Y%m%d')}_meta.json", "r") as f:
            storage_file_list = loads(f.read())
            extra_info = "<small>completion metadata loaded from local cached</small>"
    except:
        storage_file_list = [{
            "brand": "Completion metadata not available", 
            "len": "*",
            "list": [{"key": "cache not ready", "server": "-", "desc": "ERR", "uurl": "/ycrawl/joblist/checkin/"}]
        }]
        extra_info = "<small>completion meta data not yet available (run checkin?)</small>"

    pagedata=dict(
        completed_percent = f"{(1-n_todo/n_all):.2%}",
        n_jobs = f"{n_all-n_todo}/{n_all}",
        jobs_detail = f"{n_ok} completed ok<br/>{n_error}+{n_forfeit} issues",
        jobs_detail2 = f"~{n_ok/(n_all-n_todo):.0%} success rate since last checkin.<br>{extra_info}",
        all_files = storage_file_list,
        gss_link = f"https://console.cloud.google.com/storage/browser/{gsbucket}/{runmode}/{datetime.now().strftime('%Y%m/%d')}",
        gso_link = f"https://console.cloud.google.com/storage/browser/yyyaaannn-us/yCrawl_Output/{datetime.now().strftime('%Y%m')}",
    )

    return render(request, 'frontend/overview.html', pagedata)


@login_required(login_url='/admin/login/')
def job_overview_log(request):
    trail = VmTrail.objects.filter(timestamp__date=date.today()).order_by("-timestamp")
    action = VmActionLog.objects.filter(timestamp__date=date.today()).order_by("-timestamp")

    vms = set([x.vmid for x in trail])
    results = []
    for one in sorted(vms):
        if one[:10].upper() in "SELF JOBCONTROL LOCAL-TEST DATAPROCESSOR":
            continue
        results.append({
            "name": one.replace("ycrawl-", ""),
            "logs": "<br/>".join([
                f"{x.timestamp.strftime('%H:%M:%S')} [{x.event}] {x.info}" 
                for x in trail if x.vmid == one
            ])
        })

    logs = open(f"{str(BASE_DIR)}/jungle.log", "r").read().split("\n")
    results.append({
        "name": "Key-LOG",
        "logs": "<br/>".join([x.split("|")[0] for x in logs if date.today().strftime("%Y-%m-%d") in x])
    })

    return render(request, "frontend/overviewlog.html", {"logs_by_vm": results})



def job_overview_vmplot(request):
    _, vm_list = vm_list_all()

    pagedata = {"graphJSON": get_geoplot_json(
        vms=vm_list, 
        height=int(0.5 * int(request.GET["width"])), 
        width=int(request.GET["width"])
    )}
    return render(request, 'frontend/overviewvmplot.html', pagedata)


def get_geoplot_json(vms, height=380, width=600):

    short_dict = {
        "csc":{"lat": 60.2055, "lon": 24.6559, "city": "Espoo, Finland", "vendor": "CSC"},
        "fi": {"lat": 60.5693, "lon": 27.1878, "city": "Hamina, Finland", "vendor": "Google"},
        "fr": {"lat": 48.8566, "lon": -2.3522, "city": "Paris, France", "vendor": "AWS"},
        "ie": {"lat": 53.3498, "lon": -6.2603, "city": "Dublin, Ireland", "vendor": "Azure"},
        "se": {"lat": 59.3293, "lon": 18.0686, "city": "Stockholm, Sweden", "vendor": "AWS"},
        "pl": {"lat": 52.2297, "lon": 21.0122, "city": "Warsaw, Poland", "vendor": "Google"},
        "nl": {"lat": 52.3676, "lon":  4.9041, "city": "Amsterdam, Netherlands", "vendor": "Azure"},
        "processor": {"lat": 60.1,"lon": 25.6, "city": "Hamina, Finalnd (inaccurate position)", "vendor": "Google"},
    }

    std_status = lambda x: "Ready" if x in ["TERMINATED", "STOPPED", "VMDEALLOCATED", "shelved_offloaded"] else x

    vm_short = [{
        "vmid": x["vmid"],
        "lat": short_dict[x["vmid"].split("-")[-1]]["lat"],
        "lon": short_dict[x["vmid"].split("-")[-1]]["lon"],
        "Vendor": short_dict[x["vmid"].split("-")[-1]]["vendor"],
        "city": short_dict[x["vmid"].split("-")[-1]]["city"],
        "Status": std_status(x["header"].split(" ")[1]),
        "desc": x["header"].replace(" (", "<br>("),
    } for x in vms
    if x["vmid"].split("-")[-1] in short_dict]

    fig = px.scatter_geo(
        vm_short,
        lat="lat",
        lon="lon",
        symbol="Status",
        color="Vendor",
        hover_name="vmid",
        custom_data=["desc", "city"],
    )

    fig.update_geos(
        framewidth=0,
        center={"lat": 57, "lon": 10},
        showcountries=True,
        showcoastlines=False,
        countrycolor="snow",
        projection_scale=6,
    )
    fig.update_layout(
        height=height, width=width,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend={"x": 0.01, "y": 0.99}
    )
    fig.update_traces(
        marker={"size": 13},
        hovertemplate = "%{customdata[0]}<br><br><i>%{customdata[1]}</i>"
    )

    return dumps(fig, cls=PlotlyJSONEncoder)
