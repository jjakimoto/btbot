import numpy as np
import torch

from .core import BaseStrategy
from ..utils import get_data_by_name
from ..constants import BUY, SELL


class RLStrategy(BaseStrategy):
    params = (
        ('train_freq', 1),
        ('debug', False),
        ('warmup', 10000),
        ('agent', None),
        ('train_n_epochs', 1000),
        ('test_n_epochs', 30),
        ('tickers', None),
        ('keys', None),
        ('device', 'cpu'),
        ('time_display', False))

    def __init__(self):
        super(RLStrategy, self).__init__()
        self.price_data = dict()
        for ticker in self.p.tickers:
            self.price_data[ticker] = get_data_by_name(self, ticker)
        self.agent = self.p.agent
        self.current_action = None
        self.is_trained = False
        self.device = self.p.device

    def fit(self, n_epochs, step, training):
        self.agent.fit(n_epochs, step, training)

    def predict(self):
        observation = dict()
        for key in self.p.keys:
            obs = []
            # Use one previous observation
            for ticker in self.p.tickers:
                obs.append(getattr(self.price_data[ticker], key)[0])
            observation[key] = np.array(obs)
        action = self.agent.predict(observation, self.current_action)
        diff = action[1:] - self.portfolio_weight[1:]
        orders = []
        for i, amount in enumerate(diff):
            order = dict()
            if amount > 0:
                order['type'] = BUY
            elif amount < 0:
                order['type'] = SELL
            else:
                continue
            ticker = self.p.tickers[i]
            order['price_data'] = self.price_data[ticker]
            # Calculate size through close value
            price_val = self.portfolio_value * amount
            size = price_val / self.price_data[ticker].close[0]
            order['size'] = size
            orders.append(order)
        return orders

    def observe(self):
        observation = dict()
        # Cash return is 0
        returns = [0., ]
        for key in self.p.keys:
            obs = []
            # Use one previous observation for state
            for ticker in self.p.tickers:
                obs.append(getattr(self.price_data[ticker], key)[-1])
            observation[key] = np.array(obs)
        # Add returns for information
        for ticker in self.p.tickers:
            ret = self.price_data[ticker].close[0] / \
                  self.price_data[ticker].close[-1] - 1
            returns.append(ret)
        returns = np.array(returns)
        info = {'returns': returns}
        if self.current_action is None:
            prev_action = self.agent.generate_action()
            prev_action = torch.tensor(prev_action,
                                       dtype=torch.float,
                                       device=self.device)
        else:
            prev_action = self.current_action
        action = self.agent.predict(observation, prev_action)
        # Update previous action
        self.current_action = torch.tensor(action,
                                           dtype=torch.float,
                                           device=self.device)
        reward = np.sum(action * returns)
        terminal = False
        self.agent.observe(observation, action, reward, terminal, info,
                           is_store=True)

    def next(self):
        self.observe()
        self.frame_count += 1
        self.train_count += 1
        if self.warmup:
            return None
        if self.train_count >= self.p.train_freq:
            # Start training and prediction
            self.process()
            step = self.frame_count - self.p.warmup
            if not self.is_trained:
                self.fit(self.p.train_n_epochs, step, training=True)
            else:
                self.fit(self.p.test_n_epochs, step, training=False)
            self.is_trained = True
            self.train_count = 0
            orders = self.predict()
            self.execute(orders)
        if self.p.time_display:
            print(f'Time: {self.datetime.date()} {self.datetime.time()}')