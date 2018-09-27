from abc import abstractmethod

import backtrader as bt
import numpy as np

from ..constants import SELL, BUY


class BaseStrategy(bt.Strategy):
    """Define the interface of Strategy

    You have to define the following methods:

    fit(): Update strategy parameters
    predict(): Return list of orders
    observe(): Optional, store observed data to update models
    process(): Optional, Process observed data before training
    """
    def __init__(self):
        self.frame_count = 0
        self.train_count = 0
        self.model = None
        self.order_dict = dict()
        self.order_info = dict()
        self.price = None

    def observe(self):
        """Store data"""
        self.trainer.store()

    def process(self):
        pass

    @abstractmethod
    def fit(self):
        raise NotImplementedError()

    @abstractmethod
    def predict(self):
        raise NotImplementedError()

    @property
    def warmup(self):
        if hasattr(self.p, 'warmup') and self.frame_count < self.p.warmup:
            return True
        else:
            return False

    @property
    def portfolio_value(self):
        return self.broker.get_value()

    @property
    def portfolio_weight(self):
        sum_val = 0.
        weight = []
        for ticker in self.p.tickers:
            data = self.price_data[ticker]
            val = self.broker.positions[data].size * data.close[0]
            weight.append(val)
            sum_val += val
        cash_val = self.broker.get_cash()
        weight.insert(0, cash_val)
        sum_val += cash_val
        return np.array(weight) / self.broker.get_value()

    def start(self):
        self.init_value = self.broker.get_value()
        self.cash_value = self.init_value

    def next(self):
        self.observe()
        self.frame_count += 1
        self.train_count += 1
        if self.warmup:
            return None
        if self.train_count >= self.p.train_freq:
            # Start training and prediction
            self.process()
            self.fit()
            self.train_count = 0
        if self.model is not None:
            orders = self.predict()
            self.execute(orders)

    def execute(self, orders):
        for _order in orders:
            price = _order.get('price_data', self.price)
            size = _order.get('size')
            if size == 0:
                continue
            if _order['type'] == SELL:
                order = self.sell(data=price, size=size)
                self.order_info[order.ref] = _order.get('info')
            elif _order['type'] == BUY:
                order = self.buy(data=price, size=size)
                self.order_info[order.ref] = _order.get('info')

    def notify_trade(self, trade):
        if hasattr(self.p, 'display'):
            display = self.p.display
        else:
            display = True
        if display and trade.isclosed:
            dt = self.data.datetime.date()
            print('---------------------------- TRADE ---------------------------------')
            print("1: Data Name:                            {}".format(
                trade.data._name))
            print("2: Bar Num:                              {}".format(
                len(trade.data)))
            print("3: Current date:                         {}".format(dt))
            print('4: Status:                               Trade Complete')
            print('5: Ref:                                  {}'.format(
                trade.ref))
            print('6: PnL:                                  {}'.format(
                round(trade.pnl, 2)))
            print('--------------------------------------------------------------------')