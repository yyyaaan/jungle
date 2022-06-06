from json import dumps
from datetime import date, datetime
from google.cloud import storage, logging as gcplogging
from plotly.utils import PlotlyJSONEncoder
import plotly.express as px

from ycrawl.models import *




#          ____                    _   __  __             _ _             
#   _   _ / ___|_ __ __ ___      _| | |  \/  | ___  _ __ (_) |_ ___  _ __ 
#  | | | | |   | '__/ _` \ \ /\ / / | | |\/| |/ _ \| '_ \| | __/ _ \| '__|
#  | |_| | |___| | | (_| |\ V  V /| | | |  | | (_) | | | | | || (_) | |   
#   \__, |\____|_|  \__,_| \_/\_/ |_| |_|  |_|\___/|_| |_|_|\__\___/|_|   
#   |___/                                                                 


def storage_file_viewer(gsbucket, runmode, job_object):
    
    bucket = storage.Client().get_bucket(gsbucket)
    all_files = [x.name for x in bucket.list_blobs(prefix=f'{runmode}/{datetime.now().strftime("%Y%m/%d")}')]
    

    main_list = [{
        "key": x.jobid.split("_")[1],
        "server": x.vmid.vmid,
        "brand": x.weburl.split(".")[1].upper(),
        "desc": ("OK" if x.note[:1] != "X" and x.completion else "") + x.note.replace("X", ""),
        "link": [f'https://storage.cloud.google.com/{gsbucket}/{xx}' for xx in all_files if x.jobid in xx],
        "uurl": x.weburl
    } for x in job_object]

    unique_brands = set([x['brand'] for x in main_list])

    output_list = [{
        "brand": the_brand,
        "list": [x for x in main_list if x['brand'] == the_brand]
    } for the_brand in sorted(list(unique_brands))]
    
    # sort has to be done in for
    for x in output_list:
        x["len"] = f"{len([y for y in x['list'] if 'OK' in y['desc']])} of {len(x['list'])}"
        x["list"].sort(key=lambda x: x["desc"] + x["key"])

    return output_list



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
