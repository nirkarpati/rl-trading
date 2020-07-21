import datetime
import matplotlib.pyplot as plt
import numpy as np
import gym
import random
from gym import spaces
import static
from data_generators import DataGenerator


class CryptoEnv(gym.Env):
    def __init__(self, start_time, title=None):
        if title == None:
            self.title = datetime.datetime.now().strftime("%s")
        else:
            self.title = title
        self.MAX_STEPS = 30
        self.forcast_minutes = 60 * 24
        self.train_start_time = start_time - datetime.timedelta(365*2)
        self.test_start_time = start_time
        self.data_gen = DataGenerator()
        self.reward_range = (-static.MAX_ACCOUNT_BALANCE,
                             static.MAX_ACCOUNT_BALANCE)
        self.total_fees = 0
        self.total_volume_traded = 0
        self.crypto_held = 0
        self.bnb_usdt_held = static.BNBUSDTHELD
        self.bnb_usdt_held_start = static.BNBUSDTHELD
        self.episode = 1

        # Graph to render
        self.graph_reward = []
        self.graph_profit = []
        self.graph_benchmark = []

        # Action space from -1 to 1, -1 is short, 1 is buy
        self.action_space = spaces.Box(low=-1,
                                       high=1,
                                       shape=(1,),
                                       dtype=np.float16)
        # Observation space contains only the actual price for the moment
        self.observation_space = spaces.Box(low=0,
                                            high=1,
                                            shape=self.data_gen.get_env_shape(),
                                            dtype=np.float16)

    def reset(self):
        self.balance = static.INITIAL_ACCOUNT_BALANCE
        self.net_worth = static.INITIAL_ACCOUNT_BALANCE + static.BNBUSDTHELD
        self.max_net_worth = static.INITIAL_ACCOUNT_BALANCE + static.BNBUSDTHELD
        self.total_fees = 0
        self.total_volume_traded = 0
        self.crypto_held = 0
        self.bnb_usdt_held = static.BNBUSDTHELD
        self.episode_reward = 0

        # Set the current step to a random point within the data frame
        # Weights of the current step follow the square function

        self.current_step = 0


        self.current_time= self.train_start_time

        return self._next_observation()

    def _next_observation(self):
        unix_time = int(self.current_time.strftime("%s") + "000")
        obs = self.data_gen.get_env(unix=unix_time)

        return obs

    def _take_action(self, action):
        # Set the current price to a random price between open and close
        current_unix_time = int(self.current_time.strftime("%s") + "000")
        current_price = self.data_gen.get_current_price(current_unix_time)

        if action[0] > 0:
            # Buy
            crypto_bought = self.balance * action[0] / current_price
            self.bnb_usdt_held -= crypto_bought * current_price * static.MAKER_FEE
            self.total_fees += crypto_bought * current_price * static.MAKER_FEE
            self.total_volume_traded += crypto_bought * current_price
            self.balance -= crypto_bought * current_price
            self.crypto_held += crypto_bought

        if action[0] < 0:
            # Sell
            crypto_sold = -self.crypto_held * action[0]
            self.bnb_usdt_held -= crypto_sold * current_price * static.TAKER_FEE
            self.total_fees += crypto_sold * current_price * static.TAKER_FEE
            self.total_volume_traded += crypto_sold * current_price
            self.balance += crypto_sold * current_price
            self.crypto_held -= crypto_sold

        self.net_worth = self.balance + self.crypto_held * current_price + self.bnb_usdt_held

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

    def step(self, action, end=True):
        # Execute one time step within the environment
        self._take_action(action)

        self.current_time = self.current_time + datetime.timedelta(minutes=self.forcast_minutes)
        self.current_step += 1

        # Calculus of the reward
        profit = self.net_worth - (static.INITIAL_ACCOUNT_BALANCE +
                                   static.BNBUSDTHELD)

        profit_percent = profit / (static.INITIAL_ACCOUNT_BALANCE + static.BNBUSDTHELD) * 100

        start_unix_time = int(self.train_start_time.strftime("%s") + "000")
        current_unix_time = int(self.current_time.strftime("%s") + "000")
        benchmark_profit = self.data_gen.get_btc_benchmark(start_unix_time, current_unix_time)

        reward = profit_percent

        # A single episode can last a maximum of MAX_STEPS steps
        if self.current_step >= self.MAX_STEPS:
            end = True
        else:
            end = False

        done = self.net_worth <= 0 or self.bnb_usdt_held <= 0 or end

        if done and end:
            self.episode_reward = reward
            self._render_episode()
            self.graph_profit.append(profit_percent)
            self.graph_benchmark.append(benchmark_profit)
            self.graph_reward.append(reward)
            self.episode += 1

        obs = self._next_observation()

        # {} needed because gym wants 4 args
        return obs, reward, done, {}

    def render(self, print_step=False, graph=False, *args):
        profit = self.net_worth - (static.INITIAL_ACCOUNT_BALANCE +
                                   static.BNBUSDTHELD)

        profit_percent = profit / (static.INITIAL_ACCOUNT_BALANCE +
                                   static.BNBUSDTHELD) * 100

        start_unix_time = int(self.train_start_time.strftime("%s") + "000")
        current_unix_time = int(self.current_time.strftime("%s") + "000")
        benchmark_profit = self.data_gen.get_btc_benchmark(start_unix_time, current_unix_time)

        if print_step:
            filename = 'render/'+self.title+'_render.txt'
            file = open(filename, 'a')

            file.write("----------------------------------------\n")
            file.write(f'Date Time: {self.current_time}\n')
            file.write(f'Step: {self.current_step}\n')
            file.write(f'Balance: {round(self.balance, 2)}\n')
            file.write(f'Crypto held: {round(self.crypto_held, 2)}\n')
            file.write(f'Fees paid: {round(self.total_fees, 2)}\n')
            file.write(f'Volume traded: {round(self.total_volume_traded, 2)}\n')
            file.write(f'Net worth: {round(self.max_net_worth, 2)}\n')
            file.write(f'Max net worth: {round(self.max_net_worth, 2)}\n')
            file.write(f'Profit: {round(profit_percent, 2)}% ({round(profit, 2)})\n')
            file.write(f'Benchmark profit: {round(benchmark_profit, 2)}\n')
            file.close()


            print("----------------------------------------")
            print(f'Step: {self.current_step}')
            print(f'Balance: {round(self.balance, 2)}')
            print(f'Crypto held: {round(self.crypto_held, 2)}')
            print(f'Fees paid: {round(self.total_fees, 2)}')
            print(f'Volume traded: {round(self.total_volume_traded, 2)}')
            print(f'Net worth: {round(self.max_net_worth, 2)}')
            print(f'Max net worth: {round(self.max_net_worth, 2)}')
            print(f'Profit: {round(profit_percent, 2)}% ({round(profit, 2)})')
            print(f'Benchmark profit: {round(benchmark_profit, 2)}')

        # Plot the graph of the reward
        if graph:
            fig = plt.figure()
            fig.suptitle('Training graph')

            high = plt.subplot(2, 1, 1)
            high.set(ylabel='Gain')
            plt.plot(self.graph_profit, label='Bot profit')
            plt.plot(self.graph_benchmark, label='Benchmark profit')
            high.legend(loc='upper left')

            low = plt.subplot(2, 1, 2)
            low.set(xlabel='Episode', ylabel='Reward')
            plt.plot(self.graph_reward, label='reward')

            plt.show()

        return profit_percent, benchmark_profit

    def _render_episode(self, filename='render/render.txt'):
        file = open(filename, 'a')
        file.write('-----------------------\n')
        file.write(f'Episode numero: {self.episode}\n')
        file.write(f'Profit: {round(self.render()[0], 2)}%\n')
        file.write(f'Benchmark profit: {round(self.render()[1], 2)}%\n')
        file.write(f'Reward: {round(self.episode_reward, 2)}\n')
        file.close()
