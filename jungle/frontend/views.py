from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Value, CharField
from datetime import date
from logging import getLogger

from commonlib.vmmanager import vm_list_all

from ycrawl.serializers import *

logger = getLogger("frontend")

# Create your views here.
def hello(request):
    return render(request, 'frontend/index.html', {"h1text": "Hello Frontend"})


@login_required(login_url='/admin/login/')
def vm_management(request):

    # vms = VmRegistry.objects.exclude(project = "test")
    n_running, vms = vm_list_all()
    return render(request, 'frontend/vmlist.html', {"h1text": "VM list", "vm_table": vms})


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
    logs = VmActionLog.objects.filter(timestamp__gte=date.today())
    trails =  VmTrail.objects.filter(timestamp__gte=date.today())
    html = "<p>Below are abstract of Today's activity log.</p><p>"
    html += "<br/>".join([f"{x.timestamp} [{','.join([xx.vmid for xx in x.vmids.all()])}] {x.event} {x.info}" for x in logs])
    html += "</p><p>"
    html += "<br/>".join([f"{x.timestamp} {x.vmid} {x.event} {x.info}" for x in trails])
    html += "</p><p><a href='/admin/ycrawl/vmactionlog/'> Action Log</a> | <a href='/admin/ycrawl/vmtrail/'> Trails </a></p>"

    return render(request, 'frontend/index.html', {"h1text": "VM Action Submitted", "mainhtml": html})
