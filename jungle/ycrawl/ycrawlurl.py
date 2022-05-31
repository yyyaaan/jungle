from datetime import date, timedelta
from google.cloud import storage
from django.db.models import Count


from ycrawl.serializers import *



#   _  __            ____                                _                
#  | |/ /___ _   _  |  _ \ __ _ _ __ __ _ _ __ ___   ___| |_ ___ _ __ ___ 
#  | ' // _ \ | | | | |_) / _` | '__/ _` | '_ ` _ \ / _ \ __/ _ \ '__/ __|
#  | . \  __/ |_| | |  __/ (_| | | | (_| | | | | | |  __/ ||  __/ |  \__ \
#  |_|\_\___|\__, | |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__\___|_|  |___/
#            |___/                                                        
# control id is either 1, 2, 3 or 0 defines a quarter of all tasks


def meta_url_configs():
    META = YCrawlConfig.get_json_by_name("url")
    control_id = ((date.today() - date(1970,1,1)).days) % 4

    # compute range of check in dates
    range_width = int((META['date-range-max'] - META['date-range-min']) / 4)
    date_adjusted_min = META['date-range-min'] - control_id
    range_delta_days = [date_adjusted_min + control_id * range_width + x for x in range(range_width)]
    hotel_config = META['active-hotel-config']
    hotel_config["checkin-list"] = [date.today() + timedelta(days=x) for x in range_delta_days]

    # compute qatar depature days
    interval_7 = range(min(range_delta_days), max(range_delta_days), 7)
    qr_config = META['active-qr-config']
    qr_config["dep-date-list"] = [date.today() + timedelta(days=x) for x in interval_7]

    return hotel_config, qr_config



#   _   _ ____  _        ____                           _             
#  | | | |  _ \| |      / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __ 
#  | | | | |_) | |     | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__|
#  | |_| |  _ <| |___  | |_| |  __/ | | |  __/ | | (_| | || (_) | |   
#   \___/|_| \_\_____|  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|   
                                                                    
def url_qr(from1, to1, from2, to2, departure_date, layover_days):

    META = YCrawlConfig.get_json_by_name("url")
    META_IATA = META['meta-iata']

    return_date = departure_date + timedelta(days=layover_days)

    if from1 == to2 and to1 == from2:
        return f'''
        https://booking.qatarairways.com/nsp/views/showBooking.action?widget=QR
        &searchType=F&addTaxToFare=Y&minPurTime=0&upsellCallId=&allowRedemption=Y&flexibleDate=Off&bookingClass=B&tripType=R&selLang=en
        &fromStation={from1}&from={META_IATA[from1]}&toStation={to1}&to={META_IATA[to1]}
        &departingHidden={departure_date.strftime("%d-%b-%Y")}&departing={departure_date.strftime("%Y-%m-%d")}
        &returningHidden={return_date.strftime("%d-%b-%Y")}&returning={return_date.strftime("%Y-%m-%d")}
        &adults=1&children=0&infants=0&teenager=0&ofw=0&promoCode=&stopOver=NA
        '''.replace("\n", "").replace("\r", "").replace(" ", "")

    return f'''
    https://booking.qatarairways.com/nsp/views/showBooking.action?widget=MLC
    &searchType=S&bookingClass=B&minPurTime=null&tripType=M&allowRedemption=Y&selLang=EN&adults=1&children=0&infants=0&teenager=0&ofw=0&promoCode=
    &fromStation={from1}&toStation={to1}&departingHiddenMC={departure_date.strftime("%d-%b-%Y")}&departing={departure_date.strftime("%Y-%m-%d")}
    &fromStation={from2}&toStation={to2}&departingHiddenMC={return_date.strftime("%d-%b-%Y")}&departing={return_date.strftime("%Y-%m-%d")}
    '''.replace("\n", "").replace("\r", "").replace(" ", "")


def url_hotel(checkin, nights, hotel):

    META = YCrawlConfig.get_json_by_name("url")
    META_URL = META['meta-url']

    # find hotel code
    if hotel.lower() in META_URL.keys():
        code = META_URL[hotel.lower()]
    else:
        print(META_URL.keys)
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
    
    def assign_seq(self, identifier): # internal use
        self.nn += 1
        return f"{date.today().strftime('%Y%m%d')}_{identifier}{self.nn:04}"

    def assign_vm(self): # internal use
        batchnum = self.nn % self.vms.count()
        return self.vms.filter(batchnum=batchnum).first()

    def delete_a_day(self, offset=0):
        """Only used in exceptional case"""
        the_date = date.today() - timedelta(days=abs(offset))
        the_date = the_date.strftime("%Y%m%d")
        BatchJobList.objects.filter(jobid__startswith=the_date).delete()

    def register_jobs(self, force=False):
        """Called on begining of a batch job, usually once a day"""
        if VmTrail.objects.filter(vmid=self.tag).count() and not force:
            return False, "already created; use force=True to re-generate"

        if force: 
            self.delete_a_day()

        hotel_config, qr_config = meta_url_configs()

        self.nn = 0
        urls_hotel = [BatchJobList(
                jobid = self.assign_seq("H"),
                vmid = self.assign_vm(),
                weburl = url_hotel(the_date, int(the_n_h.split(",")[0]), the_n_h.split(",")[1])
            )
            for the_date in hotel_config["checkin-list"]
            for the_n_h in hotel_config["hotel-nights"]
        ]

        self.nn = 0
        urls_qr = [BatchJobList(
                jobid = self.assign_seq("Q"),
                vmid = self.assign_vm(),
                weburl = url_qr(a, b, c, d, x, qr_config["center-days"])
            )
            for a in qr_config["origins"].split(",")
            for b in qr_config["destinations"].split(",")
            for c in qr_config["destinations"].split(",")
            for d in qr_config["origins"].split(",")
            for x in qr_config["dep-date-list"]
        ]

        self.nn = 0
        # bulk write to db
        BatchJobList.objects.bulk_create(urls_hotel + urls_qr)
        VmTrail(
            vmid=self.tag, 
            event="jobs created for today", 
            info=f"register {len(urls_hotel + urls_qr)} batch jobs to DB"
        ).save()

        return True

    def register_completion(self):
        """Scan completed jobs and update DB"""
        runmode, limit_retry = YCrawlConfig.get_value('scope'), int(YCrawlConfig.get_value('max-retry'))
        dstr = date.today().strftime("%Y%m%d")
        bucket = storage.Client().get_bucket(YCrawlConfig.get_value('bucket'))

        files_in_storage = [x.name for x in bucket.list_blobs(prefix=f'{runmode}/{date.today().strftime("%Y%m/%d")}')]
        keys_completed = [dstr + "_" + x.split("_")[1] for x in files_in_storage if not x.endswith("ERR.pp")]
        keys_error = [dstr + "_" + x.split("_")[1] for x in files_in_storage if x.endswith("ERR.pp")]

        # update db, add a trail
        objs = BatchJobList.objects
        objs.filter(jobid__in=keys_completed).update(completion=True)
        for x in set(keys_error):
            if keys_error.count(x) >= limit_retry:
                objs.filter(jobid=x).update(completion=True, note=f"X{keys_error.count(x)}E")
            else:            
                objs.filter(jobid=x).update(note=f"{keys_error.count(x)}E")
        
        VmTrail(vmid="none", event="updated job status", info="completion status has been updated").save()
        
        return True

    def on_vm_completed(self):
        """when one vm completes, update status, and check all done"""

        control = VmTrail.objects.filter(vmid=self.tag)
        if control.first().event == self.done:
            return True, "all completed and processed alread, don't continue"
        
        self.register_completion()

        if (self.checkin(noloop=True)) == (True, self.done):
            # start dataprocessor
            dp_vms = VmRegistry.objects.filter(project="yCrawl", role="dataprocessor")
            vmstartstop([x.vmid for x in dp_vms], "START", "start dataprocessor on all completed")
            # double check all crawler stop
            wk_vms = VmRegistry.objects.filter(project="yCrawl", role="crawler")
            vmstartstop([x.vmid for x in wk_vms], "STOP", "confirm stopped on all completed")
            # update control item
            control.update(event=self.done)
        else:
            return False, "not yet all completed, check next time"


    def checkin(self, noloop=False):
        """scheduled call; check for remaining jobs and start, return if all completed by vm"""
        if VmTrail.objects.filter(vmid=self.tag).first().event == self.done:
            return True, "done for today, do nothing"

        remaining = (BatchJobList
            .get_today_objects()
            .filter(completion=False)
            .values('vmid')
            .annotate(todo=Count('vmid'))
        )
        limit = int(YCrawlConfig.objects.get(pk="retry-threshold").value)
        vmids = [x["vmid"] for x in remaining if x["todo"] > limit]
        if len(vmids):
            vmstartstop(vmids, "START", "checkin")
            return False, "cralwer continues"
        else:
            if not noloop:
                self.on_vm_completed()
            return True, self.done
