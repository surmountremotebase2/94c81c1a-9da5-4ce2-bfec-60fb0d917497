from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    @property
    def assets(self):
        # Request only SPY to minimize data load
        return ["SPY"]

    @property
    def interval(self):
        return "1day"

    @property
    def data(self):
        return []

    def run(self, data):
        # Just buy 100% SPY every day. No math.
        return TargetAllocation({"SPY": 1.0})