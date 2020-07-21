import random
import datetime

from env_models.naive_models import *
from env_models.news_models import *
import pymongo

class DataGenerator:
    env_dim = None
    models = []
    config = json.loads(open('config.json').read())
    client = pymongo.MongoClient(config["mongo_address"],
                                 config["mongo_port"])

    db = client["cryp_mode" + str(config["mode"])]
    historical_klines = db.historical_klines
    def __init__(self):

        # LOAD MODELS
        self.models.append(sonic())
        self.models.append(forex())
        self.models.append(sentiment())

        # SET ENVIRONMENT DIM
        shapes = [0,0]
        for model in self.models:
            d = model.get_dim()
            shapes[0] += d[0]
            shapes[1] = d[1]
        self.env_dim = (shapes[0],shapes[1])


    def get_env_shape(self):

        return self.env_dim

    def get_env(self, unix= None, online = False):
        if online:
            now = datetime.datetime.now()
            now_unix_time = int(now.strftime("%s") + "000")
            envs = []
            for model in self.models:
                envs.append(model.get_env(unix=now_unix_time))

            env = np.concatenate(envs, axis=0)
            return env
        else:
            unix = int(unix)
            envs = []
            for model in self.models:
                envs.append(model.get_env(unix=unix))

            env = np.concatenate(envs, axis=0)
            return env

    def get_current_price(self,unix):
        closestBelow = self.historical_klines.find({"Timestemp": {'$lte': unix}}).sort([("Timestemp", -1)]).limit(1)
        closestBelow = closestBelow[0]
        current_price = random.uniform(float(closestBelow['Real open']),float(closestBelow['Real close']))

        return current_price

    def get_btc_benchmark(self,start,end):

        benchmark = (self.get_current_price(end) / self.get_current_price(start) - 1) * 100
        return benchmark

if __name__ == "__main__":
    dg = DataGenerator()
    obs = dg.get_env(online=True)

    bp = 0
