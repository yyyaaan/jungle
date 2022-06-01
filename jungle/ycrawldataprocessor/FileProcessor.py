from bs4 import BeautifulSoup
from threading import Thread
from datetime import datetime
from pandas import DataFrame, concat
from google.cloud import storage

from .Cooker import *

# save big str shoulld be added, excpetion no print

class FileProcessor(Thread):
    def __init__(self, filelist, gsbucket_name, tag):
        Thread.__init__(self)
        self.filelist = filelist
        self.tag = tag
        # allocate a dedicated gsclient for speed
        self.gsbucket = storage.Client(project="yyyaaannn").get_bucket(gsbucket_name)

    def run(self):
        list_errs, list_flights, list_hotels, files_exception = [],[],[],[]

        for one_filename in self.filelist:
            try:
                one_str = self.gsbucket.get_blob(one_filename).download_as_string()
                # save_big_str(one_str)
                one_soup = BeautifulSoup(one_str, 'html.parser')
                if "_ERR" in one_filename:
                    list_errs += cook_error(one_soup)
                    continue
            except Exception as e:
                print(e)
                files_exception.append({
                    "filename": one_filename, 
                    "errm": str(e),
                    "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                })
                continue

            try:
                vendor = one_soup.qurl.string.split(".")[1]
                if vendor == "qatarairways":
                    list_flights += cook_qatar(one_soup)
                elif vendor == "marriott":
                    list_hotels += cook_marriott(one_soup)
                elif vendor == "accor":
                    list_hotels += cook_accor(one_soup)
                elif vendor == "hilton":
                    list_hotels += cook_hilton(one_soup)
                elif vendor == "fourseasons":
                    list_hotels += cook_fourseasons(one_soup)
                else:
                    raise Exception(f"\nVendor not found {vendor}")
            except Exception as e:
                print(e)
                if one_soup.vmid is None or one_soup.qurl is None or one_soup.timestamp is None:
                    print(f"Exceptionally missing vmid/qurl/timestamp {one_filename}")
                files_exception.append({
                    "filename": one_filename, 
                    "vmid": one_soup.vmid.string if one_soup.vmid is not None else "missing VMID",
                    "uurl": ".".join(one_soup.qurl.string.split(".")[1:]) if one_soup.qurl is not None else "",
                    "errm": str(e),
                    "ts": one_soup.timestamp.string if one_soup.vmid is not None else ""
                })
        # endfor
        # create dataframe according to data
        hotels_by_room, hotels_by_rate, hotels_failed = [], [], []
        for x in list_hotels:
            if len(x["room_type"]) == len(x["rate_sum"]) and len(x["rate_sum"]) == len(x["rate_avg"]):
                hotels_by_room.append(x)
            elif len(x["rate_type"]) == len(x["rate_sum"]) and len(x["rate_sum"]) == len(x["rate_avg"]):
                hotels_by_rate.append(x)
            else:
                hotels_failed.append(x)

        df_hotels_1 = DataFrame(hotels_by_rate).explode(["rate_type", "rate_sum", "rate_avg"]) if len(hotels_by_rate) else None
        df_hotels_2 = DataFrame(hotels_by_room).explode(["room_type", "rate_sum", "rate_avg"]) if len(hotels_by_room) else None


        DataFrame(list_errs).to_parquet(f"e{self.tag}.gzip", compression='gzip')
        DataFrame(list_flights).to_parquet(f"f{self.tag}.gzip", compression='gzip')
        concat([df_hotels_1, df_hotels_2]).to_parquet(f"h{self.tag}.gzip", compression='gzip')

        return True
