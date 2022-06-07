from time import sleep
from json import dumps, loads
from threading import Thread
from datetime import date, datetime, timedelta
from google.cloud import storage
from django.db.models import Count

from jungle.settings import MEDIA_ROOT
from ycrawl.serializers import *
from ycrawldataprocessor.YCrawlDataProcessor import YCrawlDataProcessor



#   _  __            ____                                _                
#  | |/ /___ _   _  |  _ \ __ _ _ __ __ _ _ __ ___   ___| |_ ___ _ __ ___ 
#  | ' // _ \ | | | | |_) / _` | '__/ _` | '_ ` _ \ / _ \ __/ _ \ '__/ __|
#  | . \  __/ |_| | |  __/ (_| | | | (_| | | | | | |  __/ ||  __/ |  \__ \
#  |_|\_\___|\__, | |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__\___|_|  |___/
#            |___/                                                        
# control id is either 1, 2, 3 or 0 defines a quarter of all tasks

def create_url_config_from_json(cfg):

    if "fixed-date-min" in cfg: # align to relative date example
        dmax = datetime.strptime(cfg['fixed-date-max'], "%Y-%m-%d").date() - date.today()
        dmin = datetime.strptime(cfg['fixed-date-min'], "%Y-%m-%d").date() - date.today()
        cfg['date-range-max'], cfg['date-range-min'] = dmax.days, dmin.days

    # all groups are divided into 4-day span
    control_id = ((date.today() - date(1970,1,1)).days) % 4

    # compute range of check in dates
    range_width = int((cfg['date-range-max'] - cfg['date-range-min']) / 4)
    date_adjusted_min = cfg['date-range-min'] - control_id
    range_delta_days = [date_adjusted_min + control_id * range_width + x for x in range(range_width)]
    hotel_config = cfg['active-hotel-config']
    hotel_config["checkin-list"] = [date.today() + timedelta(days=x) for x in range_delta_days]

    # compute qatar depature days
    interval_7 = range(min(range_delta_days), max(range_delta_days), 7)
    qr_config = cfg['active-qr-config']
    qr_config["dep-date-list"] = [date.today() + timedelta(days=x) for x in interval_7]

    return hotel_config, qr_config




#   _   _ ____  _        ____                           _             
#  | | | |  _ \| |      / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __ 
#  | | | | |_) | |     | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__|
#  | |_| |  _ <| |___  | |_| |  __/ | | |  __/ | | (_| | || (_) | |   
#   \___/|_| \_\_____|  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|   
                                                                    
def url_qr(from1, to1, from2, to2, departure_date, layover_days, booking_class="B"):

    meta_iata = YCrawlConfig.get_json_by_name("meta-iata")

    return_date = departure_date + timedelta(days=layover_days)

    if from1 == to2 and to1 == from2:
        return f'''
        https://booking.qatarairways.com/nsp/views/showBooking.action?widget=QR
        &searchType=F&addTaxToFare=Y&minPurTime=0&upsellCallId=&allowRedemption=Y&flexibleDate=Off
        &bookingClass={booking_class}&tripType=R&selLang=en
        &fromStation={from1}&from={meta_iata[from1]}&toStation={to1}&to={meta_iata[to1]}
        &departingHidden={departure_date.strftime("%d-%b-%Y")}&departing={departure_date.strftime("%Y-%m-%d")}
        &returningHidden={return_date.strftime("%d-%b-%Y")}&returning={return_date.strftime("%Y-%m-%d")}
        &adults=1&children=0&infants=0&teenager=0&ofw=0&promoCode=&stopOver=NA
        '''.replace("\n", "").replace("\r", "").replace(" ", "")

    return f'''
    https://booking.qatarairways.com/nsp/views/showBooking.action?widget=MLC
    &searchType=S&bookingClass={booking_class}
    &minPurTime=null&tripType=M&allowRedemption=Y&selLang=EN&adults=1&children=0&infants=0&teenager=0&ofw=0&promoCode=
    &fromStation={from1}&toStation={to1}&departingHiddenMC={departure_date.strftime("%d-%b-%Y")}&departing={departure_date.strftime("%Y-%m-%d")}
    &fromStation={from2}&toStation={to2}&departingHiddenMC={return_date.strftime("%d-%b-%Y")}&departing={return_date.strftime("%Y-%m-%d")}
    '''.replace("\n", "").replace("\r", "").replace(" ", "")


def url_hotel(checkin, nights, hotel):


    meta_hotel = YCrawlConfig.get_json_by_name("meta-hotel")

    # find hotel code
    if hotel.lower() in meta_hotel.keys():
        code = meta_hotel[hotel.lower()]
    else:
        logger.error(f"hotel <{hotel}> not found in {meta_hotel.keys()}")
        return "ERROR"

    checkout = checkin + timedelta(days=nights)

    # use hotel_code's length to determine hotel group
    if len(code) == 4:
        return f'https://all.accor.com/ssr/app/accor/rates/{code}/index.en.shtml?dateIn={checkin.strftime("%Y-%m-%d")}&nights={nights}&compositions=2&stayplus=false'
    if len(code) == 6:
        return f'https://reservations.fourseasons.com/choose-your-room?hotelCode={code}&checkIn={checkin.strftime("%Y-%m-%d")}&checkOut={checkout.strftime("%Y-%m-%d")}&adults=2&children=0&promoCode=&ratePlanCode=&roomAmadeusCode=&_charset_=UTF-8'
    if len(code) == 7:
        return f'https://www.hilton.com/en/book/reservation/rooms/?ctyhocn={code}&arrivalDate={checkin.strftime("%Y-%m-%d")}&departureDate={checkout.strftime("%Y-%m-%d")}&room1NumAdults=2&displayCurrency=EUR'
    if len(code) > 20:
        return f'https://www.marriott.com/search/default.mi?roomCount=1&numAdultsPerRoom=2&fromDate={checkin.strftime("%m/%d/%Y")}&toDate={checkout.strftime("%m/%d/%Y")}&{code}'


#   ____            _     _                  _       _     
#  |  _ \ ___  __ _(_)___| |_ ___ _ __      | | ___ | |__  
#  | |_) / _ \/ _` | / __| __/ _ \ '__|  _  | |/ _ \| '_ \ 
#  |  _ <  __/ (_| | \__ \ ||  __/ |    | |_| | (_) | |_) |
#  |_| \_\___|\__, |_|___/\__\___|_|     \___/ \___/|_.__/ 
#             |___/                                        

class YCrawlJobs:
    """ yCrawl Job creations """

    def __init__(self):
        self.nn = 0
        self.vms = VmRegistry.objects.filter(project="yCrawl", role="crawler")
        self.tag = "JobControl" + date.today().strftime("%Y%m%d")
        self.done = "All Done"
    
    def _assign_seq(self, identifier): # internal use
        self.nn += 1
        return f"{date.today().strftime('%Y%m%d')}_{identifier}{self.nn:04}"

    def _assign_vm(self): # internal use
        batchnum = self.nn % self.vms.count()
        return self.vms.filter(batchnum=batchnum).first()

    def delete_a_day(self, offset=0):
        """Only used in exceptional case"""
        the_date = date.today() - timedelta(days=abs(offset))
        the_date = the_date.strftime("%Y%m%d")
        BatchJobList.objects.filter(jobid__startswith=the_date).delete()

    def register_jobs(self, force=False):
        """Called on begining of a batch job, usually once a day"""
        if VmTrail.objects.filter(vmid=self.tag).count():
            if force: 
                self.delete_a_day()
            else:
                return False, "already created; use force=True to re-generate"

        # clear records older than 3 days to limit db size
        self.delete_a_day(3)

        for cfg in YCrawlConfig.get_json_by_name("job-groups")["groups"]:

            hotel_config, qr_config = create_url_config_from_json(cfg)

            self.nn = 0
            urls_hotel = [BatchJobList(
                    jobid = self._assign_seq("H" + cfg["code"]),
                    vmid = self._assign_vm(),
                    weburl = url_hotel(the_date, int(the_n_h.split(",")[0]), the_n_h.split(",")[1])
                )
                for the_date in hotel_config["checkin-list"]
                for the_n_h in hotel_config["hotel-nights"]
            ]

            self.nn = 0
            urls_qr = [BatchJobList(
                    jobid = self._assign_seq("Q" + cfg["code"]),
                    vmid = self._assign_vm(),
                    weburl = url_qr(a, b, c, d, x, qr_config["center-days"], z)
                )
                for a in qr_config["origins"].split(",")
                for b in qr_config["destinations"].split(",")
                for c in qr_config["destinations"].split(",")
                for d in qr_config["origins"].split(",")
                for x in qr_config["dep-date-list"]
                for z in qr_config["booking-class"].split(",")
            ]

            BatchJobList.objects.bulk_create(urls_hotel + urls_qr)

        VmTrail(
            vmid=self.tag, 
            event="jobs created for today", 
            info=f"register {len(urls_hotel + urls_qr)} batch jobs to DB"
        ).save()

        return True

    def register_completion(self, deletion_detection=False):
        """Scan completed jobs and update DB + save to a cached file"""
        runmode, limit_retry = YCrawlConfig.get_value('scope'), int(YCrawlConfig.get_value('max-retry'))
        bucket_name = YCrawlConfig.get_value('bucket')
        dstr = date.today().strftime("%Y%m%d")
        bucket = storage.Client().get_bucket(bucket_name)

        files_in_storage = [x.name for x in bucket.list_blobs(prefix=f'{runmode}/{date.today().strftime("%Y%m/%d")}')]
        keys_completed = [dstr + "_" + x.split("_")[1] for x in files_in_storage if not x.endswith("ERR.pp")]
        keys_error = [dstr + "_" + x.split("_")[1] for x in files_in_storage if x.endswith("ERR.pp")]

        # update db, add a trail; first reset today (to enable file deletion detection)
        if deletion_detection:
            BatchJobList.get_today_objects().update(completion=False, note="")
        objs = BatchJobList.objects
        objs.filter(jobid__in=keys_completed).update(completion=True)
        for x in set(keys_error):
            if keys_error.count(x) >= limit_retry:
                objs.filter(jobid=x).update(completion=True, note=f"X{keys_error.count(x)}E")
            else:            
                objs.filter(jobid=x).update(note=f"{keys_error.count(x)}E")
        
        # save to a json file, organized by brands
        try:
            main_list = [{
                "key": x.jobid.split("_")[1],
                "server": x.vmid.vmid,
                "brand": x.weburl.split(".")[1].upper(),
                "desc": ("OK" if x.note[:1] != "X" and x.completion else "") + x.note.replace("X", ""),
                "link": [f'https://storage.cloud.google.com/{bucket_name}/{xx}' for xx in files_in_storage if x.jobid in xx],
                "uurl": x.weburl
            } for x in BatchJobList.get_today_objects()]

            unique_brands = set([x['brand'] for x in main_list])

            output_list = [{
                "brand": the_brand,
                "list": [x for x in main_list if x['brand'] == the_brand]
            } for the_brand in sorted(list(unique_brands))]
            
            # sort has to be done in for
            for x in output_list:
                x["len"] = f"{len([y for y in x['list'] if 'OK' in y['desc']])} of {len(x['list'])}"
                x["list"].sort(key=lambda x: x["desc"] + x["key"])

            with open(f"{MEDIA_ROOT}cache/{dstr}_meta.json", "w") as f:
                f.write(dumps(output_list, indent=4))
        
        except Exception as e:
            logger.warn(f"fail to write to json due to {str(e)}")

        return True


    def on_vm_completed(self):
        """when one vm completes, update status, and check all done"""

        control = VmTrail.objects.filter(vmid=self.tag)
        if control.first().event == self.done:
            return True, "all completed and processed already, don't continue"
        
        self.register_completion()

        if (self.checkin(noloop=True)) == (True, self.done):
            logger.info("All completed for today, starting data process (see Trail)")
            VmTrail(vmid="DataProcessor", event="start locally", info="Data Processor started here").save()
            
            # avoid double calling
            if VmTrail.objects.filter(vmid=self.tag).first().event == self.done:
                logger.warn("Data processor already started but called again 1???")
                return False, "data processor already started"
            sleep(3)
            if VmTrail.objects.filter(vmid=self.tag).first().event == self.done:
                logger.warn("Data processor already started but called again 2???")
                return False, "data processor already started"

            # logging final status / upload meta to output bucket / clean db
            VmTrail.objects.filter(vmid=self.tag).update(event=self.done)
            try:
                self.final_upload_and_clean_db()
            except Exception as e:
                logger.warn(f"failed to upload completion metadata or clean db due {str(e)}")

            thread = Thread(target=run_data_processor)
            thread.start()
            return True, "data processor (threaded) has started"
        else:
            VmTrail(vmid="self", event="OnCompletion", info="not yet all completed").save()
            return False, "not yet all completed, check next time"


    def checkin(self, noloop=False):
        """scheduled call; check for remaining jobs and start, return if all completed by vm"""
        if VmTrail.objects.filter(vmid=self.tag).first().event == self.done:
            return None, "done for today, do nothing"

        # skip this checkin if just get notifydone
        lastdone = VmActionLog.objects.filter(info__icontains="notifydone").latest().timestamp
        
        if (datetime.now().astimezone() - lastdone).seconds < 180:
            VmTrail(vmid="self", event="skipped checkin", info="less than 3 minutes from last notifydone").save()
            return None, "skipped checkin"
            
        self.register_completion()
        remaining = (BatchJobList
            .get_today_objects()
            .filter(completion=False)
            .values('vmid')
            .annotate(todo=Count('vmid'))
        )
        limit = int(YCrawlConfig.objects.get(pk="retry-threshold").value)
        vmids = [x["vmid"] for x in remaining if x["todo"] > limit]
        infos = [f"{x['vmid'][7:]}-{x['todo']}" for x in remaining]

        if len(vmids):
            vmstartstop(vmids, "START", f"checkin {', '.join(infos)}")
            return False, "cralwer continues"
        else:
            if not noloop:
                self.on_vm_completed()
            return True, self.done

    def final_upload_and_clean_db(self):
        # upload final meta to output
        with open(f"{MEDIA_ROOT}cache/{date.today().strftime('%Y%m%d')}_meta.json", "r") as f:
            storage_file_list = loads(f.read())
        final_meta = {
            "job-groups": YCrawlConfig.get_json_by_name("job-groups"),
            "special-exchange-rates": YCrawlConfig.get_json_by_name("xchange-rates"),
            "file-completed": storage_file_list,
        }
        storage.Client(). \
            get_bucket(YCrawlConfig.get_value('bucket-output')). \
            blob(f"yCrawl_Output/{date.today().strftime('%Y%m')}/{date.today().strftime('%Y%m%d')}_meta.json"). \
            upload_from_string(dumps(final_meta, indent=4))

        # non-import dbs 
        VmTrail.objects.filter(vmid="self", timestamp__date=date.today()).delete()
        VmActionLog.objects \
            .filter(timestamp__date=date.today()) \
            .exclude(result__icontains="shutting down") \
            .exclude(result__icontains="starting") \
            .delete()

        # older than 9 days Trails (actions not deleted yet)
        VmTrail.objects.filter(timestamp__date__lt = (date.today() - timedelta(days=9))).delete()
        VmActionLog.objects.filter(timestamp__date__lt = (date.today() - timedelta(days=9))).delete()

        return True



def run_data_processor(offset_day=0):
    # dp_vms = VmRegistry.objects.filter(project="yCrawl", role="dataprocessor")
    # vmstartstop([x.vmid for x in dp_vms], "START", "start dataprocessor on all completed")
    
    # double check all crawler stop
    if offset_day == 0:
        wk_vms = VmRegistry.objects.filter(project="yCrawl", role="crawler")
        vmstartstop([x.vmid for x in wk_vms], "STOP", "confirm stopped on all completed")

    # call dataprocessor module
    ydp = YCrawlDataProcessor(
        scope=YCrawlConfig.get_value("scope"),
        exchange=YCrawlConfig.get_json_by_name("xchange-rates"),
        bucket_name=YCrawlConfig.get_value("bucket"),
        archive_name=YCrawlConfig.get_value("bucket-archive"),
        output_name=YCrawlConfig.get_value("bucket-output"),
        msg_endpoint=YCrawlConfig.get_value("endpoint-msg"),
        ref_date=datetime.now() - timedelta(days=abs(int(offset_day))),

    )
    ydp.start_batch_processing()
    ydp.finalize_and_summarize()

    return True