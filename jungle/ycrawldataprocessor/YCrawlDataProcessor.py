from os import listdir, remove
from bs4 import BeautifulSoup
from random import shuffle, choices
from pandas import DataFrame, concat, read_parquet, to_datetime, isna
from requests import get
from datetime import datetime, timedelta
from google.cloud import storage, bigquery
from logging import getLogger
import warnings

from .LineHelper import send_df_as_flex
from .FileProcessor import FileProcessor
from jungle.settings import MEDIA_ROOT

logger = getLogger("ycrawl")

class YCrawlDataProcessor():
    """
    List files to be processed and collect the results from FileProcessor
    Depends on FileProcessor - the multi-threading unit
    _func private; _x_func only used for another private function
    """

    def __init__(
        self, scope, exchange, bucket_name, archive_name, output_name, msg_endpoint,
        testnum=0, batch_size=200, ref_date=datetime.now(),
        force_skip_processing = False
    ):
        
        self.ref_date = ref_date
        self.force_skip_processing = force_skip_processing

        self.bucket_name = bucket_name
        self.archive_name = archive_name
        self.batch_size = batch_size
        self.xchange_rates = exchange #ecb values will be added
        
        # get file list from staging
        gsclient = storage.Client(project="yyyaaannn")
        gscb = gsclient.get_bucket(self.bucket_name)
        self.file_list = [
            x.name 
            for x in gscb.list_blobs(prefix=f"{scope}/{self.ref_date.strftime('%Y%m/')}{self.ref_date.strftime('%d')}") 
            if x.name.endswith(".pp")
        ]
        shuffle(self.file_list)

        if testnum > 0 and testnum < len(self.file_list):
            self.file_list = choices(self.file_list, k=testnum)

        # bacth control
        self.index_for_the_batch = 0
        self.cached_list = []

        # output collection
        self._upload_flag = True if testnum in [0, 9999] else False
        self._bq_client = bigquery.Client()
        self._gsbucket_output = gsclient.get_bucket(output_name)
        self.flights = None
        self.hotels = None
        self.msg_endpoint = msg_endpoint
        self.final_parquet_path = MEDIA_ROOT + "cache/" + self.ref_date.strftime("%Y%m%d") + "_"

        logger.info(f"initiated processing with {len(self.file_list)} files")


    def get_next_batch(self):
        next_index = min(self.index_for_the_batch + self.batch_size, len(self.file_list))
        file_list = self.file_list[self.index_for_the_batch : next_index]

        # tag for multithreading to save results
        tag = MEDIA_ROOT + "cache/"
        tag += self.ref_date.strftime("%m%d") 
        tag += f"_{self.index_for_the_batch:04}_{next_index:04}"
        self.cached_list.append(f"{tag}")
        
        # set for next batch
        self.index_for_the_batch = next_index
        return (next_index < len(self.file_list)), file_list, tag


    def start_batch_processing(self):

        start_time = datetime.now()

        flag, threads = True, []
        if self.force_skip_processing:
            while flag:  
                flag, filelist, tag = self.get_next_batch()
            logger.warn("Skipped processing!")
            return False

        while flag:  
            flag, filelist, tag = self.get_next_batch()
            t = FileProcessor(filelist, tag, self.bucket_name, self.archive_name, self.ref_date)
            threads.append(t)
            t.start()

        logger.info(f"Files are distributed over {len(self.cached_list)} batches")
        for t in threads:
            t.join()

        logger.info(f"Processing time in seconds: {(datetime.now() - start_time).seconds}")
        return True


    def finalize_and_summarize(self):
        if self.index_for_the_batch == 0 or len(self.cached_list) == 0:
            raise Exception("File Processor not call. Use FileProcess before calling me")
            return False

        self._get_ecb_rate()
        self._finalize_df_errs()
        self._finalize_df_hotels()
        self._finalize_df_flights()
        self._send_summary()
        self._clear_files()
        self._send_drift()
        return True

    def reset_batch(self):
        """only use in extreme case"""
        self.index_for_the_batch = 0
        return "OK"

    def _get_ecb_rate(self):
        try:
            ecb = get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore") # no xml package, warnings ignored
                soup = BeautifulSoup(ecb.text, "html.parser")
                ecb_list = [x.attrs for x in soup.select("Cube")]
            ecb_list = [{"currency": str(x["currency"]), "rate": float(x["rate"])} for x in ecb_list if 'rate' in x.keys()]
            x_list = [{"currency": str(x), "rate": float(self.xchange_rates[x])} for x in self.xchange_rates.keys()]
            # no history is hold for ecb rate
            exchange_rate = DataFrame(ecb_list + x_list)
            self._x_upload_to_bq(exchange_rate, "ECBrate", write_disposition="WRITE_TRUNCATE")
        except:
            logger.warn("ECB exchange rate NOT upated, using previous saved rates")
            exchange_rate = self._bq_client.query("select * from yyyaaannn.yCrawl.ECBrate").result().to_dataframe()

        self.xchange_rates = exchange_rate
        return True

    def _get_processed_parquets(self, ext):
        flists = []
        for x in self.cached_list:
            try:
                flists.append(read_parquet(x + ext))
            except Exception as e:
                continue

        logger.info(f"Sucessfully read {len(flists)} {ext[1:]}s...OK")
        return concat(flists)

    def _finalize_df_errs(self):
        df = self._get_processed_parquets("_e.gzip")
        if self._upload_flag:
            self._x_upload_to_bq(df, "issues")
        return True

    def _finalize_df_flights(self):
        df_flights = self._get_processed_parquets("_f.gzip")
        if df_flights.shape[0] == 0:
            logger.warn("No successful flights attempt")
            self.flights = DataFrame()
            return False, "no valid flights"

        df_flights_out = (df_flights
            .groupby(["route", "ddate", "rdate"])
            .agg(ts=("ts", max))
            .merge(df_flights, on=["route", "ddate", "rdate", "ts"], how="left")
            .merge(self.xchange_rates, left_on=["ccy"], right_on=["currency"], how="left")
        )
        df_flights_out["eur"] = round((df_flights_out["price"]/df_flights_out["rate"]).astype(float))
        df_flights_out = df_flights_out[["route", "ddate", "rdate", "eur", "ccy", "price", "ts", "vmid"]]

        fname = self.final_parquet_path + "flights.parquet.gzip"
        df_flights_out.to_parquet(fname, compression='gzip')
        if self._upload_flag:
            self._x_upload_to_bq(df_flights_out, "flights")
            blob = self._gsbucket_output.blob(f"yCrawl_Output/{self.ref_date.strftime('%Y%m')}/{fname.split('/')[-1]}")
            blob.upload_from_filename(fname)

        self.flights = df_flights_out
        logger.info(f"Flights finalized with {self.flights.shape}...OK")
        return True

    def _finalize_df_hotels(self):
        df_hotels = self._get_processed_parquets("_h.gzip")
        main_keys = ["hotel", "room_type", "rate_type", "check_in", "check_out"]
        df_hotels_out = (df_hotels
            .groupby(main_keys)
            .agg(ts=("ts", max))
            .merge(df_hotels, on=main_keys + ["ts"], how="left")
            .merge(self.xchange_rates, left_on=["ccy"], right_on=["currency"], how="left")
        )

        df_hotels_out["eur"] = round((df_hotels_out["rate_avg"]/df_hotels_out["rate"]).astype(float))
        df_hotels_out["eur_sum"] = round((df_hotels_out["rate_sum"]/df_hotels_out["rate"]).astype(float))
        df_hotels_out = df_hotels_out[df_hotels_out['eur'] > 10]
        df_hotels_out = df_hotels_out[["hotel", "room_type", "rate_type", "nights", "eur", "check_in", "check_out", "eur_sum", "ccy", "rate_avg", "rate_sum", "ts", "vmid"]]

        fname = self.final_parquet_path + "hotels.parquet.gzip"
        df_hotels_out.to_parquet(fname, compression='gzip')

        if self._upload_flag:
            self._x_upload_to_bq(df_hotels_out, "hotels")
            blob = self._gsbucket_output.blob(f"yCrawl_Output/{self.ref_date.strftime('%Y%m')}/{fname.split('/')[-1]}")
            blob.upload_from_filename(fname)

        self.hotels = df_hotels_out
        logger.info(f"Hotels finalized with {self.hotels.shape}...OK")
        return True

    def _send_summary(self):
        dff, dfh, df_list = self.flights, self.hotels, []

        if dff.shape[0] !=0:
            dff["ddate"] = to_datetime(dff.ddate)
            dff["weekstart"] = dff.ddate.dt.to_period('W').apply(lambda r: r.start_time)
            dff["title"] = "Flights to Australia on QR Business"
            for keyword in ["DXB", "Dubai", "AUH", "Abu Dhabi"]:
                dff.loc[dff['route'].str.contains(keyword),'title'] = 'QR UAE on Economy'
            df_list.append((dff
                .groupby(["title", "weekstart"], as_index=False)
                .agg(best=("eur", min))
            ))

        if dfh.shape[0] !=0:
            dfh["check_in"] = to_datetime(dfh.check_in)
            dfh["weekstart"] = dfh.check_in.dt.to_period('W').apply(lambda r: r.start_time)
            dfh["title"] = dfh["hotel"]
            df_list.append((dfh
                [(~dfh.rate_type.str.contains("Non")) & (~dfh.rate_type.str.contains("Prepay"))]
                .groupby(["title", "weekstart"], as_index=False)
                .agg(best=("eur", min))
            ))

        df_msg = concat(df_list)
        df_msg['content'] = df_msg.weekstart.dt.strftime("%b-%d") + "  " + df_msg.best.astype(str)

        send_df_as_flex(df=df_msg, text="Summary for yCrawl Outputs", msg_endpoint=self.msg_endpoint)

        return True

    def _x_upload_to_bq(self, df, short_id, write_disposition="WRITE_APPEND"):
        schema = [bigquery.SchemaField(str(x), "INT64") for x in df.columns if str(x).startswith("eur")]
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=write_disposition,
        )
        return self._bq_client.load_table_from_dataframe(
            dataframe=df, 
            destination=f"yyyaaannn.yCrawl.{short_id}", 
            job_config=job_config
        ).result()

    def _x_get_hotels_drift_by_day(self, days=1, threshold_price=10, threshold_row=30):
        """called by _send_drift"""
        df_hotels_final = self.hotels
        shorten = lambda x: " ".join(str(x).split(" ")[:3] + ["\n >"])
        tag_date = (self.ref_date - timedelta(days=days)).strftime("%Y-%m-%d")

        hotel_pre = self._bq_client.query(f"""
        select hotel, min(eur) as min_eur, count(*) as n_rows
        from yyyaaannn.yCrawl.hotels
        where substring(ts, 1, 10) = "{tag_date}"
        group by hotel
        """).result().to_dataframe()

        monitor = (df_hotels_final
            .groupby("hotel")
            .agg(mineur = ("eur", "min"), nrows = ("eur", "count"))
            .merge(hotel_pre, on=["hotel"], how="outer")
        )
        monitor["eur_drift"] = 100*(monitor["mineur"] - monitor["min_eur"])/monitor["min_eur"]
        monitor["row_drift"] = 100*(monitor["nrows"] - monitor["n_rows"])/monitor["n_rows"]

        price_drifts = [
            f"{shorten(x[0])} {x[1]:.1f}% (EUR {x[2]:.0f})" 
            for x in monitor[["hotel", "eur_drift", "mineur"]].values
            if not isna(x[1]) and abs(x[1]) > threshold_price
        ]

        row_drifts = [
            f"{shorten(x[0])} {x[1]:.1f}%" 
            for x in monitor[["hotel", "row_drift"]].values
            if not isna(x[1]) and abs(x[1]) > threshold_row
        ]

        return price_drifts, row_drifts

    def _x_get_flights_drift_by_day(self, days=1, threshold_price=10, threshold_row=30):
        """called by _send_drift"""
        df_flights_final = self.flights
        shorten = lambda x: " ".join(str(x).split(" ")[:3] + ["\n >"])
        tag_date = (self.ref_date - timedelta(days=days)).strftime("%Y-%m-%d")

        # further simplied to departure city only
        flights_pre = self._bq_client.query(f"""
        select TRIM(REGEXP_EXTRACT(route, r'\w+\s+\w+')) as departure, min(eur) as min_eur, count(*) as n_rows
        from yyyaaannn.yCrawl.flights
        where substring(ts, 1, 10) = "{tag_date}"
        group by TRIM(REGEXP_EXTRACT(route, r'\w+\s+\w+'))
        """).result().to_dataframe()

        df_flights_final["departure"] = df_flights_final['route'].str.split('|').str[0]

        monitor = (df_flights_final
            .groupby("departure")
            .agg(mineur = ("eur", "min"), nrows = ("eur", "count"))
            .merge(flights_pre, on=["departure"], how="outer")
        )
        monitor["eur_drift"] = 100*(monitor["mineur"] - monitor["min_eur"])/monitor["min_eur"]
        monitor["row_drift"] = 100*(monitor["nrows"] - monitor["n_rows"])/monitor["n_rows"]

        price_drifts = [
            f"{x[0]} {x[1]:.1f}% (EUR {x[2]:.0f})"  
            for x in monitor[["departure", "eur_drift", "mineur"]].values
            if (not isna(x[1])) and (abs(x[1]) > threshold_price)
        ]

        row_drifts = [
            f"(C{days}) {x[0]} {x[1]:.1f}%" 
            for x in monitor[["departure", "row_drift"]].values
            if (not isna(x[1])) and (abs(x[1]) > threshold_price)
        ]

        return price_drifts, row_drifts

    def _send_drift(self):
        if self.hotels.shape[0] == 0 or self.flights.shape[0] == 0:
            logger.warn("Drift will NOT be processed due to empty data")
            return False

        price1h, row1h = self._x_get_hotels_drift_by_day(1)
        price4h, row4h = self._x_get_hotels_drift_by_day(4)
        price1f, row1f = self._x_get_flights_drift_by_day(1)
        price4f, row4f = self._x_get_flights_drift_by_day(4)

        msg_df = concat([
            DataFrame({"title": "-Hotel price change", "content": price4h}),
            DataFrame({"title": "-Flight price change", "content": price4f}),
            DataFrame({"title": "Hotel vs yesterday", "content": price1h}),
            DataFrame({"title": "Flight vs yesterday", "content": price1f}),
            DataFrame({"title": "_Data quantity d-4", "content": row4h + row4f}),
            DataFrame({"title": "_Data quantity d-1", "content": row1h + row1f}),
        ])

        send_df_as_flex(
            df=msg_df, msg_endpoint=self.msg_endpoint, text="Data Drift Summary", 
            color="11", size="xxs", sort=True)

        return True

    def _clear_files(self):
        [
            remove(MEDIA_ROOT + "cache/" + x)
            for x in listdir(MEDIA_ROOT + "cache/")
            if self.ref_date.strftime('%m%d_') in x and x.endswith(".gzip")
        ]
        return True
