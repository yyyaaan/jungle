from django.shortcuts import render

from .models import *
from .scripts import *

# Create your views here.
def myweb(request):
    active_tasks = WebTasks.objects.filter(isactive=True)
    for task in active_tasks:        
        t = WebReaderThreaded(task)
        t.start()

    return render(request, 'minimal.html', {"mainhtml": "<h3>hello<h3>"})


def start_multi_webs():

    return True


def load_data_once():
    # to align previous appdata.json to here
    import json
    prev = json.load(open("/home/yan/jungle/zz0.json"))

    newj = [{
        "model": "webreader.webtasks",
        "pk": 1000+i,
        "fields": {
            "isactive": True,
            "group": "KunnanTontti",
            "webaddress": one["link"],
            "keyfield": one["key"],
            "display": one["city"],
            "note": "",
        }
    } for i, one in enumerate(prev["kunnan-tontti"])]
    with open("toload.json", "w") as f:
        f.write(json.dumps(newj, indent=4))


