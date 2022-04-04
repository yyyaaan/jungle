# to be called by Crontab hourly, exact timing is managed here to simplify tasks

from os import environ
from datetime import datetime
from requests import post

BASE_URL = "http://127.0.0.1:8000/ycrawl/"
AUTH = {"Authorization": environ['djangobearer']}

def simplepost(ext, json=None):
    return post(BASE_URL+ext, headers=AUTH, json=json)

def cron_scheduled_jobs(hour=datetime.utcnow().hour):

    if hour == 0:
        res = simplepost("START/")

    if hour in range(1,15):
        # res = simplepost("CHECKIN/")
        pass

    res = simplepost("START/", {"stop": True})
    print(res.status_code)


if __name__ == "__main__":
    cron_scheduled_jobs(hour=datetime.utcnow().hour)


