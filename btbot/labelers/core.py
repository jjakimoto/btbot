from abc import abstractmethod

import backtrader as bt


class BaseLabeler(bt.Indicator):
    """Abstract class for labeler

    Parameters
    ----------
    sider: Class for deciding side, optional
    sider_params: dict, optional
        Parameters for instanciating sider class
    """
    params = (('sider', None),
              ('sider_params', dict()))

    def __init__(self):
        if self.is_metalabeling:
            self.lines.side = self.p.sider(**self.p.sider_params)

    @property
    def current_side(self):
        if self.p.sider is None:
            return None
        else:
            return int(self.lines.side[0])

    def get_side(self, i):
        if self.p.sider is None:
            return None
        else:
            return int(self.lines.side[i])

    @property
    def is_metalabeling(self):
        if self.p.sider is None:
            return False
        else:
            return True

    @abstractmethod
    def next(self):
        raise NotImplementedError()
