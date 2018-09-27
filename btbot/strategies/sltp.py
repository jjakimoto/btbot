import xgboost as xgb
import pyfolio as pf
from sklearn.preprocessing import StandardScaler
import numpy as np
import backtrader as bt

from ..utils import print_trade_analysis, get_data_by_name
from ..trainer import Trainer
from ..indicators import EMAVolatility
from .core import BaseStrategy
from ..feeders import PriceVolumeFeeder
from ..samplers import BasicSampler
from ..labelers import SLTPLabeler
from ..constants import SELL, BUY, SHORT, LONG, HOLD
from ..configs import xgb_params


class SLTPStrategy(BaseStrategy):
    params = (
        ('warmup', 200),
        ('train_freq', 1),
        ('size', 50),
        ('debug', False),
        ('min_data', 5),
        ('max_data', 100000),
        ('timelag', 10),
        ('num_round', 50),
        ('sider', None),
        ('sider_params', dict()),
        ('sampler', BasicSampler),
        ('sampler_params', dict()),
        ('labeler', SLTPLabeler),
        ('stls', 1),
        ('tkpf', 1),
        ('model_params', xgb_params),
        ('labeler_params', dict(period=20, forward=5)))

    def __init__(self):
        super(SLTPStrategy, self).__init__()
        self.price = get_data_by_name(self, 'price')
        self.feeder = PriceVolumeFeeder(self.price, 10)
        self.sampler = self.p.sampler(**self.p.sampler_params)
        # Add sider for labeler
        self.p.labeler_params['sider'] = self.p.sider
        self.p.labeler_params['sider_params'] = self.p.sider_params
        # barrier parameters
        self.p.labeler_params['stls'] = self.p.stls
        self.p.labeler_params['tkpf'] = self.p.tkpf
        self.labeler = self.p.labeler(**self.p.labeler_params)
        self.trainer = Trainer(self.feeder, self.labeler)
        self.vol_lines = EMAVolatility().lines.vol
        self.scaler = StandardScaler()

    def fit(self):
        if self.is_metalabeling:
            side = self.labeler.current_side
        else:
            side = None
        features, labels = self.trainer.get_data(side=side)
        if len(features) == 0:
            return None
        features = self.scaler.fit_transform(features)
        labels = np.array(self.transform_labels(labels))
        dtrain = xgb.DMatrix(features, label=labels)
        self.model = xgb.train(self.p.model_params, dtrain, self.p.num_round)

    def predict(self):
        # Prediction
        pred_features = np.array([self.feeder.current_feed])
        pred_features = self.scaler.transform(pred_features)
        dtest = xgb.DMatrix(pred_features)
        signal = self.model.predict(dtest)
        signal = self.inverse_transform_labels(signal)[0]
        self.current_signal = signal
        info = dict()
        info['take_profit'] = self.labeler.current_take_profit
        info['stop_loss'] = self.labeler.current_stop_loss
        if self.is_metalabeling:
            side = self.labeler.current_side
            if side == SHORT and signal == 1:
                order = [{'type': SELL, 'size': self.p.size, 'info': info}]
            elif side == LONG and signal == 1:
                order = [{'type': BUY, 'size': self.p.size, 'info': info}]
            else:
                order = []
        else:
            if signal == SHORT:
                order = [{'type': SELL, 'size': self.p.size, 'info': info}]
            elif signal == LONG:
                order = [{'type': BUY, 'size': self.p.size, 'info': info}]
            else:
                order = []
        return order

    @property
    def is_metalabeling(self):
        return self.labeler.is_metalabeling

    def transform_labels(self, labels):
        map_dict = {SHORT: 0, HOLD: 1, LONG: 2}
        return [map_dict[int(x)] for x in labels]

    def inverse_transform_labels(self, labels):
        map_dict = {0: SHORT, 1: HOLD, 2: LONG}
        return [map_dict[int(x)] for x in labels]

    def print_result(self):
        pnl = self.broker.get_value() - self.init_value
        total_ret = pnl / self.init_value
        year_count = float(self.frame_count) / 252.
        avg_ret = (total_ret + 1) ** (1. / year_count) - 1
        print('PnL: ', pnl)
        print(f'Total Return: {total_ret * 100}%')
        print(f'Annual Average Return: {avg_ret * 100}%')
        print_trade_analysis(self)

    def print_pyfolio(self, strategy):
        pyfolio = strategy.analyzers.getbyname('pyfolio')
        returns, positions, transactions, gross_lev = pyfolio.get_pf_items()
        pf.create_full_tear_sheet(
            returns,
            positions=positions,
            transactions=transactions,
            round_trips=True)

    def notify_order(self, order):
        if order.status == bt.Order.Completed:
            # If there is name in the info, that would be Take Profit or Stop Loss order
            if 'name' in order.info:
                self.broker.cancel(self.order_dict[order.ref])
            else:
                info = self.order_info[order.ref]
                if order.isbuy():
                    stop_loss = order.executed.price * (
                                1.0 - info['stop_loss'])
                    take_profit = order.executed.price * (
                                1.0 + info['take_profit'])

                    stls_ord = self.sell(exectype=bt.Order.Stop,
                                         price=stop_loss)
                    stls_ord.addinfo(name="Stop Loss")

                    tkpf_ord = self.sell(exectype=bt.Order.Limit,
                                         price=take_profit)
                    tkpf_ord.addinfo(name="Take Profit")
                    self.order_dict[stls_ord.ref] = tkpf_ord
                    self.order_dict[tkpf_ord.ref] = stls_ord
                elif order.issell():
                    stop_loss = order.executed.price * (
                                1.0 + info['stop_loss'])
                    take_profit = order.executed.price * (
                                1.0 - info['take_profit'])

                    stls_ord = self.buy(exectype=bt.Order.Stop,
                                        price=stop_loss)
                    stls_ord.addinfo(name="Stop Loss")

                    tkpf_ord = self.buy(exectype=bt.Order.Limit,
                                        price=take_profit)
                    tkpf_ord.addinfo(name="Take Profit")
                    self.order_dict[stls_ord.ref] = tkpf_ord
                    self.order_dict[tkpf_ord.ref] = stls_ord