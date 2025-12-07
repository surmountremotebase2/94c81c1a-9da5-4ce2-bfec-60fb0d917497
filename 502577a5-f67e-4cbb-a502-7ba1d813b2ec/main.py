from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        self.sectors = [
            "XLK", "XLF", "XLV", "XLY", "XLP", "XLE", "XLI", "XLB", "XLU", 
            "XLRE", "XLC"
        ]
        # We need IYR to act as the "stunt double" for XLRE before 2015
        self.proxies = {"XLRE": "IYR"} 
        
        # We request data for ALL sectors + the proxy
        self.tickers = self.sectors + ["IYR"]

    @property
    def interval(self):
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        return []

    def run(self, data):
        if not data or "ohlcv" not in data:
            return TargetAllocation({})
        
        allocation_dict = {}
        performance = {}
        lookback = 126  # 6 Months

        for sector in self.sectors:
            # 1. Determine which ticker to check for data
            # Default to the normal sector ticker
            check_ticker = sector 
            
            # If the normal ticker is missing data (e.g., XLRE before 2015), try the proxy
            if sector in self.proxies:
                if sector not in data["ohlcv"] or len(data["ohlcv"][sector]) < lookback:
                    check_ticker = self.proxies[sector]

            # 2. Check if we have data for whatever ticker we decided to use
            if check_ticker not in data["ohlcv"]:
                continue # Skip XLC before 2018 (it has no proxy, so we just ignore it)
            
            ticker_data = data["ohlcv"][check_ticker]
            
            if len(ticker_data) > lookback:
                current = ticker_data[-1]["close"]
                past = ticker_data[-lookback]["close"]
                momentum = (current - past) / past
                performance[sector] = momentum # We store it under the original name "XLRE"
            else:
                continue

        # 3. Rank and Trade
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_sectors) >= 2:
            # Pick Top 2
            top_2 = [sorted_sectors[0][0], sorted_sectors[1][0]]
            
            # LOGIC FIX: If the winner is "XLRE" but we are in 2010, we must buy "IYR"
            final_orders = []
            for pick in top_2:
                # If we picked XLRE, but XLRE doesn't exist yet, buy IYR
                if pick == "XLRE" and "XLRE" not in data["ohlcv"]:
                    final_orders.append("IYR")
                else:
                    final_orders.append(pick)
            
            log(f"Top Sectors: {top_2} -> Buying: {final_orders}")
            
            for asset in final_orders:
                allocation_dict[asset] = 0.5

        return TargetAllocation(allocation_dict)
        return TargetAllocation(allocation_dict)