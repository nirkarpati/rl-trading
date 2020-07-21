import json

import numpy as np
import pandas as pd
import pymongo
from sklearn.preprocessing import MinMaxScaler

class sonic:
    config = json.loads(open('config.json').read())
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode" + str(config["mode"])]
    historical_klines = db.historical_klines
    scaler = MinMaxScaler()
    def __init__(self):
        records = list(self.historical_klines.find({}).limit(3000))
        df = pd.DataFrame(records)
        df = df.drop(['_id', 'Symbol',"Timestemp","Close time","Ignore","Open time","Real open","Real close"], axis=1)
        arr = np.array(df)
        self.scaler.fit(arr)
    def get_dim(self):

        return (9,10)
    def get_env(self, unix= None, online = False):
        if online:
            obs = self.get_online_obs()

            return obs
        else:
            closestBelow = self.historical_klines.find({"Timestemp": {'$lte': unix}}).sort([("Timestemp", -1)]).limit(self.get_dim()[1])

            closestBelow = list(closestBelow)

            df = pd.DataFrame(closestBelow)
            df = df.drop(['_id', 'Symbol',"Timestemp","Close time","Ignore","Open time","Real open","Real close"], axis=1)
            obs = np.array(df)

            obs = self.scaler.transform(obs).T
            return obs

    def get_online_obs(self):

        return


class forex:
    config = json.loads(open('config.json').read())
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode" + str(config["mode"])]
    historical_usd_forex = db.historical_usd_forex
    scaler = MinMaxScaler()
    def __init__(self):
        records = list(self.historical_usd_forex.find({}).limit(3000))
        df = pd.DataFrame(records)
        df = df.drop(['_id',"Timestemp"], axis=1)
        arr = np.array(df)
        self.scaler.fit(arr)
    def get_dim(self):

        return (42,10)

    def get_env(self, unix= None, online = False):
        if online:
            obs = self.get_online_obs()

            return obs
        else:
            closestBelow = self.historical_usd_forex.find({"Timestemp": {'$lte': unix}}).sort([("Timestemp", -1)]).limit(self.get_dim()[1])

            closestBelow = list(closestBelow)

            df = pd.DataFrame(closestBelow)
            df = df.drop(['_id',"Timestemp"], axis=1)
            obs = np.array(df)

            obs = self.scaler.transform(obs).T
            return obs
    def get_online_obs(self):

        return