from random import shuffle
from datetime import date, timedelta
from google.cloud import storage

from ycrawl.models import *



#   _  __            ____                                _                
#  | |/ /___ _   _  |  _ \ __ _ _ __ __ _ _ __ ___   ___| |_ ___ _ __ ___ 
#  | ' // _ \ | | | | |_) / _` | '__/ _` | '_ ` _ \ / _ \ __/ _ \ '__/ __|
#  | . \  __/ |_| | |  __/ (_| | | | (_| | | | | | |  __/ ||  __/ |  \__ \
#  |_|\_\___|\__, | |_|   \__,_|_|  \__,_|_| |_| |_|\___|\__\___|_|  |___/
#            |___/                                                        
# control id is either 1, 2, 3 or 0 defines a quarter of all tasks

# META is now saved into two major parts "general" an "url"
def meta_major():
    META = YCrawlConfig.get_json_by_name("general")
    return META['bucket'], META['scope'], META['max-retry']


def meta_url_configs():
    META = YCrawlConfig.get_json_by_name("url")
    control_id = ((date.today() - date(1970,1,1)).days) % 4

    # compute range of check in dates
    range_width = int((META['date-range-max'] - META['date-range-min']) / 4)
    date_adjusted_min = META['date-range-min'] - control_id
    range_delta_days = [date_adjusted_min + control_id * range_width + x for x in range(range_width)]
    HOTEL_CONFIG = META['active-hotel-config']
    HOTEL_CONFIG["checkin-list"] = [date.today() + timedelta(days=x) for x in range_delta_days]

    # compute qatar depature days
    interval_7 = range(min(range_delta_days), max(range_delta_days), 7)
    QR_CONFIG = META['active-qr-config']
    QR_CONFIG["dep-date-list"] = [date.today() + timedelta(days=x) for x in interval_7]

    return HOTEL_CONFIG, QR_CONFIG





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


#   _   _ ____  _        ____                    _ _             _             
#  | | | |  _ \| |      / ___|___   ___  _ __ __| (_)_ __   __ _| |_ ___  _ __ 
#  | | | | |_) | |     | |   / _ \ / _ \| '__/ _` | | '_ \ / _` | __/ _ \| '__|
#  | |_| |  _ <| |___  | |__| (_) | (_) | | | (_| | | | | | (_| | || (_) | |   
#   \___/|_| \_\_____|  \____\___/ \___/|_|  \__,_|_|_| |_|\__,_|\__\___/|_|   
                                                                             

def get_keys_status():
    
    GSBUCKET, RUN_MODE, LIMIT_RETRY = meta_major()
    DATE_STR = date.today().strftime("%Y%m%d")

    gcp_client = storage.Client()
    bucket = gcp_client.get_bucket(GSBUCKET)
    files_in_storage = [x.name for x in bucket.list_blobs(
        prefix=f'{RUN_MODE}/{date.today().strftime("%Y%m/%d")}')]

    keys_completed = [
        DATE_STR + "_" + x.split("_")[1] for x in files_in_storage if not x.endswith("ERR.pp")]
    # error keys may have duplicates, limit retry to remove it
    keys_error = [DATE_STR + "_" + x.split("_")[1]
                  for x in files_in_storage if x.endswith("ERR.pp")]
    keys_forfeit = [
        x for x in keys_error if keys_error.count(x) >= LIMIT_RETRY]
    keys_forfeit = list(dict.fromkeys(keys_forfeit))  # remove dup

    return keys_completed, keys_forfeit, keys_error


def assign_seq(identifier):
    global NN
    NN += 1
    return f"{date.today().strftime('%Y%m%d')}_{identifier}{NN:04}"


def fetch_all_urls(shuffled=True):
    HOTEL_CONFIG, QR_CONFIG = meta_url_configs()

    global NN
    NN = 0
    urls_hotel = [{
        "key": assign_seq("H"),
        "url": url_hotel(the_date, int(the_n_h.split(",")[0]), the_n_h.split(",")[1])
    }
        for the_date in HOTEL_CONFIG["checkin-list"]
        for the_n_h in HOTEL_CONFIG["hotel-nights"]
    ]

    NN = 0
    urls_qr = [{
        "key": assign_seq("Q"),
        "url": url_qr(a, b, c, d, x, QR_CONFIG["center-days"])
    }
        for a in QR_CONFIG["origins"].split(",")
        for b in QR_CONFIG["destinations"].split(",")
        for c in QR_CONFIG["destinations"].split(",")
        for d in QR_CONFIG["origins"].split(",")
        for x in QR_CONFIG["dep-date-list"]
    ]

    all_urls = urls_hotel + urls_qr
    if shuffled:
        shuffle(all_urls)

    return all_urls


def call_url_coordinator(batch=999, total_batches=1, no_check=False, type="ONE"):
    urls_all = fetch_all_urls()

    if batch < total_batches:
        urls_all = [x for x in urls_all if (int(x['key'][-4:]) % total_batches == batch)]

    if no_check:
        bash_nodes = [f'node node_handler.js {x["key"]} "' + x['url'] + '"' for x in urls_all]
        output = "\n".join(bash_nodes) if type == "ONE" else bash_nodes
        return output

    keys_done, keys_forfeit, keys_error = get_keys_status()
    urls_todo = [x for x in urls_all if x['key'] not in (keys_done + keys_forfeit)]

    if type == "INFO":
        info_str = f"Planned={len(urls_all)}, Todo={len(urls_todo)}, Completion={len(keys_done)}({len(set(keys_done))}), Error={len(keys_error)}({len(set(keys_error))}), X={len(keys_forfeit)}"
        return info_str, len(urls_all), len(urls_todo), len(keys_done), len(keys_forfeit), len(keys_error), len(set(keys_error))

    bash_nodes = [f'node node_handler.js {x["key"]} "' + x['url'] + '"' for x in urls_todo]    
    output = "\n".join(bash_nodes) if type == "ONE" else bash_nodes
    return output


