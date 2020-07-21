import json
import datetime

import requests
from currency_converter import CurrencyConverter
from binance.client import Client
import pandas as pd
import keys
import os
import pymongo
from readability import Document
from bs4 import BeautifulSoup

config = json.loads(open('config.json').read())


def get_page_text( html ):
    news_article = Document( html )
    summary_html = news_article.summary()
    dom = BeautifulSoup(summary_html, 'html.parser')
    text = dom.get_text('\n', True)

    return text


def download_symbol_from_binance(symbol="BTCUSDT",days_ago=2):
    #Changes these values to obtain the desired csv
    pair = os.getenv("PAIR", symbol)
    since = os.getenv("SINCE", str(days_ago)+" day ago UTC")


    #Connect to the Binance client
    client = Client(keys.apiKey, keys.secretKey)

    # Get the data from Binance
    df = client.get_historical_klines(pair, Client.KLINE_INTERVAL_1MINUTE, since)

    # Store the open and close values in a pandas dataframe
    real_values = []
    for i in df:
        real_values.append([i[1], i[3],i[0]])

    real_df = pd.DataFrame(real_values, columns=["Real open", "Real close","Timestemp"])


    # Transform the data to a pandas array
    df = pd.DataFrame(df,
                      columns=[
                          "Open time", "Open", "High", "Low", "Close", "Volume",
                          "Close time", "Quote asset volume", "Number of trades",
                          "Taker buy base asset volume",
                          "Taker buy quote asset volume", "Ignore"
                      ])

    # Add the real open and the real close to df
    df = pd.concat([df, real_df], axis=1)

    # Remove the last timestep
    df = df[:-1]

    records = list(df.T.to_dict().values())




    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode"+str(config["mode"])]
    collection = db.historical_klines


    for record in records:
        record["Symbol"] = symbol
        collection.update_one({'Timestemp': record["Timestemp"],"Symbol":record["Symbol"]},
                                      {'$set': record},
                                      upsert=True)


def download_forex_from_ecCentralBank(days_ago=2):
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode"+str(config["mode"])]
    collection = db.historical_usd_forex


    c = CurrencyConverter()
    symbols_list = c.currencies
    for i in range(0,days_ago):
        try:
            record = {}
            d = datetime.date.today() - datetime.timedelta(i)
            for symbol in symbols_list:
                try:
                    record[symbol] = c.convert(1, symbol, 'USD', date=d)
                except:
                    record[symbol] = -1

            record["Timestemp"] = int(d.strftime("%s")+"000")

            collection.update_one({'Timestemp': record["Timestemp"]},
                                  {'$set': record},
                                  upsert=True)

        except Exception as e :
            if str(e) != "USD is not a supported currency":
                print (e)
            else:
                print (symbol)


    return


def download_news(from_unix=None,to_unix=None, keywords=[]):
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode"+str(config["mode"])]
    collection = db.news

    today = datetime.datetime.now()
    unix_time = int(today.strftime("%s") + "000")
    _delta = int(unix_time) - int(from_unix)
    _delta = int((_delta/1000 / 60 / 60) /24)

    delta_ = int(from_unix) - int(to_unix)
    delta_ = int((delta_/1000 / 60 / 60) /24) + 1

    for i in range(_delta,(delta_+_delta)):
        print (i)
        print ((i-_delta)/(delta_))
        try:
            d_start = datetime.datetime.now() - datetime.timedelta(i)
            d_end = datetime.date.today() - datetime.timedelta(i-1)
            d_start = d_start.strftime("%Y%m%d").replace("-","") + "000000"
            d_end = d_end.strftime("%Y%m%d").replace("-", "") + "000000"

            query = 'https://api.gdeltproject.org/api/v2/doc/doc?sort=DateDesc&mode=artlist&maxrecords=250&format=json&mode=artlist&startdatetime='+d_start+'&enddatetime='+d_end+'&max_records=100&query=sourcelang:english'
            asset_repeat = 'repeat2:"bitcoin"'
            query = query + " " + asset_repeat

            search_terms = keywords
            if len(search_terms) > 1:
                search_terms = " OR ".join(search_terms)
                search_terms = '(' + search_terms + ')'
                query = query + " " + search_terms
            elif len(search_terms) == 1:
                search_terms = " OR ".join(search_terms)

                query = query + " " + search_terms




            res = requests.get(query)
            res = res.content
            res = eval(res)
            for article in res["articles"]:
                try:
                    response = requests.get(url=article["url"], timeout=20)
                    html = response.text
                    text = get_page_text(html)
                    finbert_response = requests.post("http://localhost:5002/",json={"text":text})
                    if finbert_response.status_code == 200:
                        _finbert_payload = eval(finbert_response.text)
                        sum = 0
                        for sent in _finbert_payload:
                            sum += sent['sentiment_score']
                        score_body = sum/len(_finbert_payload)
                    else:
                        score_body = 0

                    finbert_response = requests.post("http://localhost:5002/",json={"text":article["title"]})
                    if finbert_response.status_code == 200:
                        finbert_payload = eval(finbert_response.text)
                        sum = 0
                        for sent in finbert_payload:
                            sum += sent['sentiment_score']
                        score_headline = sum/len(finbert_payload)
                    else:
                        score_headline = 0

                    score = (score_headline + score_body) / 2
                    date_time_obj = datetime.datetime.strptime(article["seendate"], '%Y%m%dT%H%M%SZ')
                    bp = 9
                    article["Timestemp"] = int(date_time_obj.strftime("%s")+"000")
                    article["finbert_score"] = score
                    article["finbert_predictions"] = {
                        "body":_finbert_payload,
                        "headline":finbert_payload
                    }
                    article["search_term"] = "bitcoin"
                    collection.update_one({'Timestemp': article["Timestemp"],"title":article["title"]},
                                          {'$set': article},
                                          upsert=True)
                except Exception as e:
                    print("Failed Article: ", str(e))
        except Exception as e:
            print("Failed Day: ", str(e))

    return

if __name__ == "__main__":

    s = 1044
    e = 3*365
    d_start = datetime.date.today() - datetime.timedelta(s)
    d_end = datetime.date.today() - datetime.timedelta(3*365)
    d_start = int(d_start.strftime("%s") + "000")
    d_end = int(d_end.strftime("%s") + "000")

    download_news(from_unix=d_start,to_unix=d_end,keywords=[])
