import numpy as np

from .core import BaseFeeder


class PriceVolumeFeeder(BaseFeeder):
    def __init__(self, price, period):
        self.price = price
        self.period = period

    def get_feed(self, idx=0):
        features = []
        features.append(
            np.array(self.price.close.get(ago=idx, size=self.period)) /
            self.price.close[idx])
        features.append(
            np.array(self.price.volume.get(ago=idx, size=self.period)) /
            self.price.volume[idx])
        if len(features) == 0:
            return None
        else:
            return np.hstack(features)