import backtrader as bt

from ..constants import SHORT, LONG, HOLD


class CrossOverSider(bt.Indicator):
    """Cross over to determine the side for metalabeling"""
    lines = ('side',)
    params = (
        # period for the fast Moving Average
        ('fast', 10),
        # period for the slow moving average
        ('slow', 50),
        # moving average to use
        ('_movav', bt.indicators.SMA)
    )

    def __init__(self):
        sma_fast = self.p._movav(period=self.p.fast, plot=False, subplot=False)
        sma_slow = self.p._movav(period=self.p.slow, plot=False, subplot=False)

        self.crossover = bt.indicators.CrossOver(sma_fast, sma_slow,
                                                 plot=False, subplot=False)

    def next(self):
        if self.crossover[0] < 0:
            self.lines.side[0] = SHORT
        elif self.crossover[0] > 0:
            self.lines.side[0] = LONG
        else:
            self.lines.side[0] = HOLD
