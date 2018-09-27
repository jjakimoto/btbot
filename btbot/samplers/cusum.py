import backtrader as bt

from ..indicators import EMAVolatility


class CUSUMFilter(bt.Indicator):
    lines = ('signal', 'vol',)
    plotlines = dict(signal=dict(_plotskip=True,),
                     vol=dict(_plotskip=True,))
    params = (('period', 100),
              ('scale', 1),
              ('devfactor', 1))

    def __init__(self):
        self.sum_pos = 0
        self.sum_neg = 0
        self.init_pos = None
        self.init_neg = None
        self.lines.vol = EMAVolatility(self.data,
                                       period=self.p.period,
                                       scale=self.p.scale)
        self.threshold = 0.

    def next(self):
        if not self.init_pos or not self.init_neg:
            self.init_pos = self.data[0]
            self.init_neg = self.data[0]
            self.lines.signal[0] = 1
            self.threshold = self.vol[0] * self.p.devfactor
        else:
            self.sum_pos = max(0, self.sum_pos + (
                        self.data[0] - self.data[-1]) / self.init_pos)
            self.sum_neg = min(0, self.sum_neg + (
                        self.data[0] - self.data[-1]) / self.init_neg)
            if self.sum_neg < -self.threshold:
                self.init_neg = self.data[0]
                self.sum_neg = 0
                self.lines.signal[0] = 1
                self.threshold = self.vol[0] * self.p.devfactor
            elif self.sum_pos > self.threshold:
                self.init_pos = self.data[0]
                self.sum_pos = 0
                self.lines.signal[0] = 1
                self.threshold = self.vol[0] * self.p.devfactor
            else:
                self.lines.signal[0] = 0