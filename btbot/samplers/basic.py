import backtrader as bt


class BasicSampler(bt.Indicator):
    lines = ('signal',)
    plotlines = dict(signal=dict(_plotskip=True,))

    def next(self):
        self.lines.signal[0] = 1
