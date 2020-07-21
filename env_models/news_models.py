import json

import numpy as np
import pymongo
from sklearn.preprocessing import MinMaxScaler


class sentiment:
    config = json.loads(open('config.json').read())
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode" + str(config["mode"])]
    news = db.news
    scaler = MinMaxScaler()
    def __init__(self):
        records = list(self.news.find({},{"finbert_predictions":1,"finbert_score":1}).limit(3000))
        records = [[x["finbert_predictions"]["headline"][0]['sentiment_score'],x['finbert_score']] for x in records]
        arr = np.array(records)
        self.scaler.fit(arr)
    def get_dim(self):

        return (2,10)

    def get_env(self, unix= None, online = False):
        if online:
            obs = self.get_online_obs()

            return obs
        else:
            closestBelow = self.news.find({"Timestemp": {'$lte': unix}}).sort([("Timestemp", -1)]).limit(self.get_dim()[1])

            closestBelow = list(closestBelow)

            records = [[x["finbert_predictions"]["headline"][0]['sentiment_score'],x['finbert_score']] for x in closestBelow]
            obs = np.array(records)

            obs = self.scaler.transform(obs).T
            return obs

    def get_online_obs(self):

        return