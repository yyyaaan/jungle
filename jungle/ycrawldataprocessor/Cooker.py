from pandas import DataFrame
from datetime import datetime
import re

# supporting lambdas, note for use of comma and dot
extract_float = lambda x: float(re.sub(r"[^\d]+", "", x)) 
get_float = lambda x: float(re.sub(r"[^\d\.]+", "", x.replace(",", ".")))
parse_floats = lambda x: [get_float(xx.get_text()) for xx in x]
parse_ccy = lambda x: "EUR" if "€" in x[0].get_text() else "USD"
parse_texts = lambda x: [xi.get_text(strip=True) for xi in x]


###############################################################################################
#   ____      _                      _     _     _            __       _ ____   ___  _   _     
#  |  _ \ ___| |_ _   _ _ __ _ __   | |   (_)___| |_    ___  / _|     | / ___| / _ \| \ | |___ 
#  | |_) / _ \ __| | | | '__| '_ \  | |   | / __| __|  / _ \| |_   _  | \___ \| | | |  \| / __|
#  |  _ <  __/ |_| |_| | |  | | | | | |___| \__ \ |_  | (_) |  _| | |_| |___) | |_| | |\  \__ \
#  |_| \_\___|\__|\__,_|_|  |_| |_| |_____|_|___/\__|  \___/|_|    \___/|____/ \___/|_| \_|___/
### Some JSON further contain explodable array in values #######################################

def cook_marriott(soup):
    if soup.flag.string != "Available":
        raise Exception("Unavailable or sold out")
    
    cico = [datetime.strptime(x, "%a, %b %d, %Y").date() 
        for x in soup.select_one("#staydates").select_one("div.is-visible").get_text(strip=True).split("―")]

    # each room type, contains array!
    json_list = [{
        "hotel": soup.find("h1").get_text(strip=True),
        "room_type": room.select_one("h3.l-margin-bottom-none").get_text(strip=True),
        "rate_type": [x.get_text(strip=True) for x in room.select('h3.description')],
        "rate_avg": [extract_float(x['data-totalpricebeforetax']) for x in room.select("div.l-rate-inner-container")],
        "rate_sum": [extract_float(x['data-totalprice']) for x in room.select("div.l-rate-inner-container")],
        "ccy": room.select_one("span.nightly.t-nightly").get_text(strip=True).split(" ")[0],
        "check_in": cico[0],
        "check_out": cico[1],
        "nights": int((cico[1] - cico[0]).days),
        "vmid": soup.vmid.string,
        "ts": soup.timestamp.string
    } for room in soup.select("div.room-rate-results.rate-type.t-box-shadow")]

    # explode(["rate_type", "rate_avg", "rate_sum"])
    return json_list


def cook_accor(soup):
    if soup.flag.string != "Available":
        raise Exception("Unavailable or sold out")

    cico = [datetime.strptime(x.strip(), "%B %d, %Y").date()
            for x in soup.select_one("p.basket-hotel-info__stay").get_text().split("\n") if x.strip() !=""]

    nights = int((cico[1] - cico[0]).days)

    # Accor sometimes report pre-tax value as Per night, formula differs
    calc_sum = lambda a, b: a + b
    if "per night" in soup.select_one("div.price-block__composition-info").get_text():
        calc_sum = lambda a, b: a*nights + b

    json_list = [{
        "hotel": soup.select_one("h3.basket-hotel-info__title").get_text(strip=True),
        "room_type": room.select_one("h2").get_text(strip=True),
        "rate_type": [x.select_one("span").get_text(strip=True) for x in room.select(".offer__options")],
        #"rate_sum_pre": parse_floats(room.select(".offer__price")),
        #"rate_sum_tax": parse_floats(room.select(".pricing-details__taxes")),
        "rate_avg": [calc_sum(a,b)/nights for a,b in zip(parse_floats(room.select(".offer__price")), 
                                        parse_floats(room.select(".pricing-details__taxes")))],
        "rate_sum": [calc_sum(a,b) for a,b in zip(parse_floats(room.select(".offer__price")), 
                                        parse_floats(room.select(".pricing-details__taxes")))],
        "ccy": parse_ccy(room.select(".offer__price")),
        "check_in": cico[0],
        "check_out": cico[1],
        "nights": nights,
        "vmid": soup.vmid.string,
        "ts": soup.timestamp.string
    } for room in soup.select("li.list-complete-item")]
    
    # explode(["rate_type", "rate_sum", "rate_avg"])
    return json_list


def cook_hilton(soup):
    if soup.flag.string != "Available":
        raise Exception("Unavailable or sold out")

    # year is not printed in MOST cases
    cico = soup.select_one("[data-testid='stayDates']").get_text(strip=True).split("– ")
    the_year = cico[1].split(",")[-1]
    cico[0] = cico[0].strip() + "," + the_year if len(cico[0]) < 18 else cico[0]
    cico = [datetime.strptime(x, "%a, %b %d, %Y").date() for x in cico]

    # two types of rates listed (either one should be available)
    rates = soup.select("[data-testid='moreRatesButton']") + soup.select("[data-testid='quickBookPrice']")
    nights = int((cico[1] - cico[0]).days)

    json_data = {
        "hotel": soup.select_one("span.relative.inline-block").get_text(strip=True),
        "room_type": [x.get_text(strip=True) for x in soup.select("[data-testid='roomTypeName']")],
        "rate_type": "Best Rate Advertised",
        "rate_avg": parse_floats(rates),
        "rate_sum": [x * nights for x in parse_floats(rates)],
        "ccy": parse_ccy(rates),
        "check_in": cico[0],
        "check_out": cico[1],
        "nights": nights,
        "vmid": soup.vmid.string,
        "ts": soup.timestamp.string
    }
    
    # explode(["rate_type", "rate_sum", "rate_avg"])
    return [json_data]


def cook_fourseasons(soup):
    price_str = [x.get_text(strip=True) for x in soup.select("div.price > div > .fullprice")]
    cico = soup.select_one(".search-summary__form-field--check-in-check-out > div").get_text().split(" - ")
    cico = [datetime.strptime(x.strip(), "%m/%d/%Y").date() for x in cico]

    nights = int((cico[1] - cico[0]).days)

    json_data = {
        "hotel": "Four Seasons " + soup.select_one("div.search-summary__form-field__value").get_text(strip=True),
        "room_type": [x.get_text(strip=True) for x in soup.select(".room-item-title")],
        "rate_type": "Best Rate Advertised",
        "rate_avg": [float(re.sub(r"[^\d\.]+", "", x)) for x in price_str],
        "rate_sum": [float(re.sub(r"[^\d\.]+", "", x)) * nights for x in price_str],
        "ccy": price_str[0][0:3],
        "check_in": cico[0],
        "check_out": cico[1],
        "nights": nights,
        "vmid": soup.vmid.string,
        "ts": soup.timestamp.string
    }

    # explode(["room_type", "rate_avg", "rate_sum"])
    return [json_data]



def cook_qatar(soup):
    r_num = re.compile("\d{3,6}\.\d{0,2}")
    r_ccy = re.compile("[A-Z]{3}")
            
    cities = [x.get_text(strip=True) for x in soup.select(".ms-city")]
    trip_pair = [(x.get_text(strip=True), x['onclick'].split(",")[1:]) for x in soup.select("a.csBtn")]

    json_list = [{
        "ccy": r_ccy.findall(prices)[0],
        "price": float(r_num.findall(prices)[0]),
        "ddate": min([datetime.strptime(dates[0], "'%a %b %d %X %Z%z %Y'").date(), datetime.strptime(dates[1], "'%a %b %d %X %Z%z %Y')").date()]),
        "rdate": max([datetime.strptime(dates[0], "'%a %b %d %X %Z%z %Y'").date(), datetime.strptime(dates[1], "'%a %b %d %X %Z%z %Y')").date()]),
        "route": f"{cities[0]} {cities[1]}|{cities[2]} {cities[3]}" if len(cities) == 4 else f"{cities[0][:-2]} {cities[1]}|{cities[1]} {cities[0][:-2]}",
        "vmid": soup.vmid.string,
        "ts": soup.timestamp.string,
    } for (prices, dates) in trip_pair]

    # single item
    return json_list


def cook_error(soup):
    # single json, single item
    return [{
        "vmid": soup.vmid.string,
        "uurl": ".".join(soup.qurl.string.split(".")[1:]),
        "errm": parse_texts(soup.timestamp.next_elements)[-1],
        "ts": soup.timestamp.string
    }]