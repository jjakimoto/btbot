import pandas as pd
import backtrader as bt


class EMAVolatility(bt.Indicator):
    lines = ('vol',)
    params = (('period', 100),
              ('scale', 1))

    def next(self):
        data = pd.Series(self.data.get(size=self.p.period))
        ret = data.pct_change().dropna() * self.p.scale
        vol = ret.ewm(span=self.p.period - 1).std().values
        if len(vol) == 0:
            self.lines.vol[0] = 0
        else:
            self.lines.vol[0] = vol[-1]