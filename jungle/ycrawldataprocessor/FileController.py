from os import system
from bs4 import BeautifulSoup
from json import dumps, loads
from random import shuffle, choices
from pandas import DataFrame, concat
from datetime import datetime
from google.cloud import storage

from ycrawl.models import YCrawlConfig

# EX_RATES = META["special-exchange-rates"]

class FileController():

    def __init__(self, testnum=0):
        # values from DB
        bucket = YCrawlConfig.get_value("bucket")
        bucket_output = YCrawlConfig.get_value("bucket-output")
        bucket_archive = YCrawlConfig.get_value("bucket-archive")
        scope = YCrawlConfig.get_value("scope")
        dt = datetime.now()

        gsc = storage.Client(project="yyyaaannn")
        self.UPLOAD = True if testnum in [0, 9999] else False
        self.SCOPE = scope
        self.BUCKET_NAME = bucket
        self.GS_STAGING = gsc.get_bucket(bucket)
        self.GS_OUTPUTS = gsc.get_bucket(bucket_output)
        self.GS_ARCHIVE = gsc.get_bucket(bucket_archive)
        
        # get file list from staging
        self.FILE_LIST = [
            x.name 
            for x in self.GS_STAGING.list_blobs(prefix=f"{self.SCOPE}/{dt.strftime('%Y%m/')}{dt.strftime('%d')}") 
            if x.name.endswith(".pp")
        ]
        shuffle(self.FILE_LIST)

        if testnum > 0 and testnum < len(self.FILE_LIST):
            self.FILE_LIST = choices(self.FILE_LIST, k=testnum)

        # bacth control
        self.index_for_the_batch = 0

    def get_next_batch(self, size=200):
        next_index = min(self.index_for_the_batch + size, len(self.FILE_LIST))
        file_list = self.FILE_LIST[self.index_for_the_batch : next_index]
        self.index_for_the_batch = next_index
        return (next_index < len(self.FILE_LIST)), file_list

    def reset_batch(self):
        self.index_for_the_batch = 0
        return "OK"
        
