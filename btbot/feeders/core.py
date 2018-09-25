from abc import ABC, abstractmethod


class BaseFeeder(ABC):
    @abstractmethod
    def get_feed(self, idx=0):
        """Implement the method to get feed at idx"""

    @property
    def current_feed(self):
        return self.get_feed(0)