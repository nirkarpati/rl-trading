import datetime

import os

from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines import PPO2

from env import CryptoEnv

number_of_months = 10
title = datetime.datetime.now().strftime("%s")
for i in range(number_of_months):
    j = number_of_months - i

    train_start_date = datetime.date.today() - datetime.timedelta(days=j*30)

    train_unix_time = int(train_start_date.strftime("%s") + "000")  # Second as a decimal number [00,61] (or Unix Timestamp)


    env = DummyVecEnv([lambda: CryptoEnv(train_start_date,title=title)])

    # Instanciate the agent
    model = PPO2(MlpPolicy, env, gamma=0.1, learning_rate=0.0001, verbose=1, tensorboard_log="./gym-cryp_tensorboard/")

    # Train the agent
    total_timesteps = int(os.getenv('TOTAL_TIMESTEPS', 500000))
    model.learn(total_timesteps)

    # Render the graph of rewards
    env.render()

    # Save the agent
    model.save('PPO2_CRYPTO')

    # Trained agent performance
    obs = env.reset()
    env.render()

    for i in range(30):
        action, _states = model.predict(obs)
        obs, rewards, done, info = env.step(action)
        env.render(print_step=True)
