from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # 1. Define your Universe clearly
        self.tickers = [
            "XLK", "XLF", "XLV", "XLY", "XLP", 
            "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC"
        ]
        # Log to confirm this specific code is running
        log("Initialize Sector Strategy...")

    @property
    def interval(self):
        # "1day" is best for sector rotation
        return "1day"

    @property
    def assets(self):
        # This tells the engine WHICH data to fetch. 
        # If this list is wrong, data["ohlcv"] will be empty.
        return self.tickers

    @property
    def data(self):
        # Return empty list if you only need OHLCV data
        return []

    def run(self, data):
        # 2. Safety Check: Ensure we actually have data
        if not data or "ohlcv" not in data:
            log("No data received.")
            return TargetAllocation({})
        
        allocation_dict = {}
        performance = {}
        lookback = 126  # 6 Months

        # 3. Calculate Momentum
        for ticker in self.tickers:
            # Safe access to OHLCV data
            ohlcv_data = data["ohlcv"]
            
            # Check if this specific ticker has data in the bundle
            # Note: data["ohlcv"] is a list of dictionaries like [{'AAPL': ...}, {'GOOG': ...}] 
            # OR a dictionary of lists depending on version. 
            # In standard Surmount, it is usually a list of dicts.
            
            # Helper to get close prices for this ticker specifically
            ticker_closes = [x[ticker]["close"] for x in ohlcv_data if ticker in x]

            if len(ticker_closes) > lookback:
                current = ticker_closes[-1]
                past = ticker_closes[-lookback]
                momentum = (current - past) / past
                performance[ticker] = momentum
            else:
                performance[ticker] = -999 # Ignore assets with insufficient history

        # 4. Rank and Select Top 2
        # Sort by momentum descending
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        
        # Filter out the -999s
        valid_sectors = [x for x in sorted_sectors if x[1] > -999]

        if len(valid_sectors) >= 2:
            top_2 = [valid_sectors[0][0], valid_sectors[1][0]]
            log(f"Top Sectors: {top_2}")
            
            for ticker in top_2:
                allocation_dict[ticker] = 0.5
        else:
            log("Not enough valid data to trade.")

        return TargetAllocation(allocation_dict)