from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from markdown import markdown

from .models import *
from .scripts import *

def my(request):
    
    objs, rendered = MarkItDown.objects.all().filter(enabled=True), []
    rendered = [markdown(obj.md) for obj in objs]
    docs = [{
        "url": str(x.doc.url).replace("/media", "https://yan.fi"), 
        "desc": x.desc,
        "size": f"{x.doc.size/1024/1024: 0.2f}M",
    } for x in MyDoc.objects.all().order_by("desc")]

    return render(request, 'webreader/index.html', {"htmls": rendered, "docs": docs})


def myweb(request):
    return render(request, 'webreader/webreader.html', {
        "groups": WebTasks.objects.all().values("group").distinct(),
    })


def update_results(request):
    # within 15 minutes prior to last run
    mintime = WebReader.objects.latest().timestamp - timedelta(minutes=15)
    records = WebReader.objects.filter(timestamp__gte=mintime)

    htmldata = {
        "summary": f"{records.count()} reading since UAT {mintime.strftime('%H:%M %b-%d')}",
        "updates": records.filter(status="Updated"),
        "others": records.exclude(status__in=["Updated", "OK"]),
    }

    return render(request, 'webreader/webresults.html', htmldata)


@login_required(login_url='/admin/login/')
def start_multi_webs(request):
    req = request.GET if request.method == "GET" else request.POST
    tasks = WebTasks.objects.filter(isactive=True)

    if "group" in req and req["group"] != "All":
        tasks = tasks.filter(group=req["group"])

    for task in tasks:        
        t = WebReaderThreaded(task)
        t.start()

    txtout = f'starting new web reading for group {req["group"]}'
    return render(request, 'minimal.html', {"mainhtml": txtout})
