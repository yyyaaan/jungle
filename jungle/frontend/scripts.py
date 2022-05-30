from json import dumps
from datetime import datetime
from google.cloud import storage, logging as gcplogging
from plotly.utils import PlotlyJSONEncoder
import plotly.express as px

from ycrawl.ycrawlurlmaker import *


#          ____                    _   __  __             _ _             
#   _   _ / ___|_ __ __ ___      _| | |  \/  | ___  _ __ (_) |_ ___  _ __ 
#  | | | | |   | '__/ _` \ \ /\ / / | | |\/| |/ _ \| '_ \| | __/ _ \| '__|
#  | |_| | |___| | | (_| |\ V  V /| | | |  | | (_) | | | | | || (_) | |   
#   \__, |\____|_|  \__,_| \_/\_/ |_| |_|  |_|\___/|_| |_|_|\__\___/|_|   
#   |___/                                                                 


def storage_file_viewer():
    
    GSBUCKET, RUN_MODE, _ = meta_major()
    
    bucket = storage.Client().get_bucket(GSBUCKET)
    all_files = [x.name for x in bucket.list_blobs(prefix=f'{RUN_MODE}/{datetime.now().strftime("%Y%m/%d")}')]
    info_str = "All scheduled tasks done." if len([x for x in all_files if "meta_on_completion" in x]) else "In progress..."
        
    all_uurls = fetch_all_urls()
    uurls_by_key = dict([(x['key'].split("_")[1], x['url']) for x in all_uurls])

    revert_batch = dict([
        (x.batchnum, x.vmid) for x in 
        VmRegistry.objects.filter(project="yCrawl", role="crawler")
    ])

    main_list_draft = [{
        "key": the_key,
        "batchn": int(the_key[1:]) % len(revert_batch),
        "link": [f'https://storage.cloud.google.com/{GSBUCKET}/{x}' for x in all_files if f"_{the_key}_" in x],
        "uurl": uurls_by_key[the_key]
    } for the_key in [x['key'].split("_")[1] for x in all_uurls] ]

    count_err_ok = lambda lst: f"{len([y for y in lst if 'ERR' not in y])}OK{len([y for y in lst if 'ERR' in y])}E"

    main_list = [{
        "key": x["key"],
        "server": revert_batch[x["batchn"]],
        "brand": x["uurl"].split(".")[1].upper(),
        "desc": count_err_ok(x["link"]).replace("0E", "").replace("1OK","OK").replace("0OK", ""),
        "link": x["link"],
        "uurl": x["uurl"]
    } for x in main_list_draft]

    unique_brands = set([x['brand'] for x in main_list])

    output_list = [{
        "brand": the_brand,
        "list": [x for x in main_list if x['brand'] == the_brand]
    } for the_brand in sorted(list(unique_brands))]
    
    # sort has to be done in for
    for x in output_list:
        x["len"] = f"{len([y for y in x['list'] if 'OK' in y['desc']])} of {len(x['list'])}"
        x["list"].sort(key=lambda x: x["desc"] + x["key"])

    return output_list, info_str


def get_simple_log():

    log_client = gcplogging.Client()

    TODAY0 = f"{date.today().strftime('%Y-%m-%d')}T00:00:00.123456Z"

    the_filter = f'logName="projects/yyyaaannn/logs/stdout" AND timestamp>="{TODAY0}"'
    log_entries = log_client.list_entries(filter_=the_filter, order_by=gcplogging.DESCENDING)
    logs_stdout = [f'{x.timestamp.strftime("%H:%M:%S")} {x.payload}' for x in log_entries]
    logs_stdout = [x for x in logs_stdout if "!DOCTYPE html" not in x]

    ### logs orginized by server
    the_filter = f'logName="projects/yyyaaannn/logs/y_simple_log" AND timestamp>="{TODAY0}"'
    log_entries = log_client.list_entries(filter_=the_filter, order_by=gcplogging.DESCENDING)
    log_simplified = [f'{x.timestamp.strftime("%H:%M:%S")}{x.payload}' for x in log_entries if not str(x.payload).startswith("test")]
    log_simplified = [x for x in log_simplified if "!DOCTYPE html" not in x]

    logs_by_vm = [{"name": "App-Engine", "logs": "<br/>".join(logs_stdout)}]
    for the_vm in [x.vmid for x in VmRegistry.objects.filter(project="yCrawl", role="crawler")]:
        the_log_entries = [x.replace(the_vm, "") for x in log_simplified + logs_stdout if the_vm in x and "VM Manager" not in x]
        the_log = {
            "name": the_vm.upper().replace("YCRAWL-", ""),
            "logs": "<br/>".join(sorted(the_log_entries, reverse=True)),
        }
        logs_by_vm.append(the_log)

    

    return  logs_by_vm




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

    def std_status(x): return "Ready" if x in ["TERMINATED", "STOPPED", "VMDEALLOCATED", "shelved_offloaded"] else x

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
