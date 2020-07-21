import datetime
import pymongo

from data_downloader import *

config = json.loads(open('config.json').read())
client = pymongo.MongoClient(config["mongo_address"],
                             config["mongo_port"])

db = client["cryp_mode" + str(config["mode"])]

def refresh_database():
    now = datetime.datetime.now()
    now_unix_time = int(now.strftime("%s") + "000")

    news_limits = get_historical_database_limits(db.news)

    download_news(from_unix=news_limits["end_unix"], to_unix=now_unix_time, keywords=[])


    historical_klines_limits = get_historical_database_limits(db.historical_klines)
    download_symbol_from_binance(days_ago=historical_klines_limits["_delta"])

    forex_limits = get_historical_database_limits(db.historical_usd_forex)
    download_forex_from_ecCentralBank(days_ago=forex_limits["_delta"])




    return True


def get_historical_database_limits(collection):
    now = datetime.datetime.now()
    now_unix_time = int(now.strftime("%s") + "000")
    latest = collection.find({}, {"Timestemp": 1}).sort([("Timestemp", -1)]).limit(1)[0]["Timestemp"]
    oldest = collection.find({}, {"Timestemp": 1}).sort([("Timestemp", 1)]).limit(1)[0]["Timestemp"]

    delta_ = int(now_unix_time) - int(latest)
    delta_ = int((delta_/1000 / 60 / 60) /24)

    payload = {
        "start_unix":oldest,
        "end_unix":latest,
        "_delta":delta_
    }

    return payload


refresh_database()