from flask import Flask
from flask_cors import CORS
import time
from flask import request
from stable_baselines import PPO2

from data_generators import DataGenerator

app = Flask(__name__)
CORS(app)
start = int(round(time.time()))
model = PPO2.load("PPO2_CRYPTO.zip")
data_generator = DataGenerator()


@app.route("/action",methods=['GET'])
def action():
    payload = request.get_json()
    # TODO get obs
    obs = data_generator.get_env(online=True)
    action, _states = model.predict(obs)

    response = {
        "action":action.tolist(),
        "_states": _states
    }
    return response, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
