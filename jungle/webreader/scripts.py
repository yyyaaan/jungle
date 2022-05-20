import requests, json, difflib, os, random
from datetime import date
from bs4 import BeautifulSoup
from threading import Thread

from .models import *

class WebReaderThreaded(Thread):
    def __init__(self, webtask):
        Thread.__init__(self)
        self.webtask = webtask

    def read_webpage(self):
        webpage = requests.get(self.webtask.webaddress)
        websoup = BeautifulSoup(webpage.text, 'html.parser')
        main_content = websoup.select(self.webtask.keyfield)
        extracted_text = main_content[0].get_text() if len(main_content)  else "xxx"
        return extracted_text.strip()

    def read_cached(self):
        lastobj = WebReader.objects.filter(task=self.webtask).order_by("timestamp").last()
        content = "xxx" if lastobj is None else lastobj.response
        return content

    def write_to_cache(self, content, status, info=""):
        new = WebReader(task=self.webtask, response=content, status=status, info=info)
        new.save()
    
    def run(self):
        try:
            the_text = self.read_webpage()
        except Exception as e:
            the_text = "x"
            self.write_to_cache("", "Fail to read", str(e)[:254])
            return False

        if len(the_text) < 10: 
            self.write_to_cache("", "Content Error", the_text)
            return False

        # compare new one and old one
        prev_text = self.read_cached()
        str_del, str_add = "", ""
        for i,s in enumerate(difflib.ndiff(prev_text, the_text)):
            # location i text s[-1]
            if s[0]=='-' and s[-1] !="\r": str_del += s[-1]
            if s[0]=='+' and s[-1] !="\r": str_add += s[-1]

        # notifiy and write when diff recognized
        if len(str_del + str_add) > 3:
            self.write_to_cache(the_text, "Updated", info=f"ADD: {str_add}; DEL: {str_del}")
        else:
            self.write_to_cache(the_text, "OK")
        return True

        