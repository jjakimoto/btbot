import numpy as np


class Trainer(object):
    def __init__(self, feeder, labeler):
        self.feeder = feeder
        self.labeler = labeler
        # Note that we store only feed not label
        self.store_feed = []

    def store(self):
        feed = self.feeder.current_feed
        if feed is not None and len(feed) > 0:
            self.store_feed.append(feed)

    def get_data(self, num_data=None, side=None):
        if num_data is None:
            num_data = self.num_data
        num_data = min(self.num_data, num_data)
        feeds = []
        labels = []
        for i in range(num_data):
            label = self.labeler.get_label(-i, side)
            if label is None:
                continue
            feeds.append(self.store_feed[-(i + 1)])
            labels.append(label)
        return np.array(feeds), np.array(labels).astype(int)

    @property
    def num_data(self):
        return len(self.store_feed)