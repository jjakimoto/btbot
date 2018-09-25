from ..indicators import EMAVolatility
from ..constants import LONG, SHORT, HOLD, NONE
from ..utils import get_data_by_name
from .core import BaseLabeler


class SLTPLabeler(BaseLabeler):
    """Abstract class for labeler

    Parameters
    ----------
    period: int, (default 10)
        Period to take average for estimating volatility
    horizon: int, (default 10)
        Horizontal threshold for labeling
    sltp: list
        Stop Loss and Take Profit scale
    sider: Class for deciding side, optional
    size: int, (default 10)
        The size of betting
    sider_params: dict, optional
        Parameters for instanciating sider class
    """
    lines = ('label', 'time_diff', 'vol', 'side',
             'take_profit', 'stop_loss')
    plotlines = dict(label=dict(_plotskip=True,),
                     time_diff=dict(_plotskip=True,),
                     vol=dict(_plotskip=True,),
                     side=dict(_plotskip=True,),
                     take_profit=dict(_plotskip=True,),
                     stop_loss=dict(_plotskip=True,))
    params = (('period', 10),
              ('scale', 1.),
              ('horizon', 10),
              ('stls', 1),
              ('tkpf', 1),
              ('size', 10),
              ('sider', None),
              ('sider_params', dict()))

    def __init__(self):
        super(SLTPLabeler, self).__init__()
        self.price = get_data_by_name(self, 'price')
        self.lines.vol = EMAVolatility(self.price,
                                       period=self.p.period)

    def next(self):
        self.lines.label[0] = NONE
        self.lines.stop_loss[0] = self.p.stls * self.vol[0]
        self.lines.take_profit[0] = self.p.tkpf * self.vol[0]
        for i in range(1, self.p.horizon + 1):
            idx = -i
            if self.lines.label[idx] == NONE:
                diff = (self.price[0] - self.price[idx]) / self.price[idx]
                if self.p.tkpf > 0:
                    tkpf = self.vol[idx] * self.p.tkpf
                else:
                    tkpf = None
                if self.p.stls > 0:
                    stls = -self.vol[idx] * self.p.stls
                else:
                    stls = None
                # Set threashold depending on the side
                if self.is_metalabeling:
                    side = self.lines.side[idx]
                    diff *= side
                    if tkpf is not None:
                        tkpf *= side
                    if stls is not None:
                        stls *= side
                if tkpf is not None and diff > tkpf:
                    self.lines.label[idx] = self.tkpf_label
                    self.lines.time_diff[idx] = i
                elif stls is not None and diff < stls:
                    self.lines.label[idx] = self.stls_label
                    self.lines.time_diff[idx] = i
                elif i == self.p.horizon:
                    self.lines.label[idx] = self.hold_label
                    self.lines.time_diff[idx] = i

    def get_label(self, idx=0, side=None):
        label = self.lines.label[idx]
        time_diff = self.lines.time_diff[idx]
        if label != NONE and time_diff <= (-idx):
            if not self.is_metalabeling or side == self.side[idx]:
                return label
            else:
                return None
        else:
            return None

    @property
    def current_take_profit(self):
        return self.take_profit[0]

    @property
    def current_stop_loss(self):
        return self.stop_loss[0]

    @property
    def tkpf_label(self):
        return 1

    @property
    def stls_label(self):
        if self.is_metalabeling:
            return 0
        else:
            return -1

    @property
    def hold_label(self):
        return 0
