from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler
import pandas as pd
import backtrader as bt

from .cerebro import Cerebro


def get_data_by_name(obj, name):
    """Get data by name within indicators or strategies

    Parameters
    ----------
    obj: Indicator or Strategy instance
    name: str
        data mame

    Returns
    DataFeed
    """
    tgt_data = None
    for data in obj.datas:
        if data._name == name:
            tgt_data = data
            break
    if tgt_data is None:
        raise Exception(f'You should define data named {name}')
    else:
        return tgt_data


class PandasNormalizer(BaseEstimator, TransformerMixin):
    def __init__(self, scaler=StandardScaler()):
        self.scaler = scaler

    def fit(self, X, y=None):
        X_array = X.values.astype(float)
        self.scaler.fit(X_array, y)
        return self

    def transform(self, X):
        X_array = self.scaler.transform(X.values.astype(float))
        df = pd.DataFrame(X_array, columns=X.columns, index=X.index)
        return df

    def inverse_transform(self, X):
        X_array = self.scaler.inverse_transform(X.values.astype(float))
        df = pd.DataFrame(X_array, columns=X.columns, index=X.index)
        return df


def print_trade_analysis(strategy):
    # SharpeRatio
    sr_analyzer = strategy.analyzers.getbyname('sharpe').get_analysis()
    print(f'Annual SharpeRatio: {round(sr_analyzer["sharperatio"], 2)}')
    # DrawDwon
    dd_analyzer = strategy.analyzers.getbyname('drawdown').get_analysis()
    print(f'Maximum DrawDown: {round(dd_analyzer.max.drawdown, 2)} %')
    print(f'Maximum MoneyDown: {round(dd_analyzer.max.moneydown, 2)}')
    print(f'Maximum Drawdown Length: {dd_analyzer.max.len}')


def get_cerebro(startcash=10000):
    cerebro = Cerebro()
    cerebro.broker.setcash(startcash)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpe',
                        timeframe=bt.analyzers.TimeFrame.Days)
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    return cerebro