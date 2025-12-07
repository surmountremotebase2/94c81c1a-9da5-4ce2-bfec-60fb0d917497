from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # We REMOVED 'XLC' and 'XLRE' so this can run back to 1999/2000.
        self.sectors = [
            "XLK", # Technology
            "XLF", # Financials
            "XLV", # Health Care
            "XLY", # Consumer Discretionary
            "XLP", # Consumer Staples
            "XLE", # Energy
            "XLI", # Industrials
            "XLB", # Materials
            "XLU"  # Utilities
        ]
        
        self.tickers = self.sectors
        log("Strategy Loaded: Classic 9 Sectors (Long History Compatible)")

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
        # 1. Safety Check
        if not data or "ohlcv" not in data:
            return TargetAllocation({})
        
        ohlcv_full = data["ohlcv"]
        if len(ohlcv_full) < 10:
            return TargetAllocation({})

        # 2. Optimization (Last 200 days only)
        lookback = 126
        buffer = 20
        if len(ohlcv_full) > (lookback + buffer):
            relevant_data = ohlcv_full[-(lookback + buffer):]
        else:
            relevant_data = ohlcv_full

        allocation_dict = {}
        performance = {}

        # 3. Calculate Momentum
        for sector in self.sectors:
            sector_closes = []
            
            for day_data in relevant_data:
                if sector in day_data:
                    val = day_data[sector]["close"]
                    sector_closes.append(float(val))
            
            if len(sector_closes) >= lookback:
                current_price = sector_closes[-1]
                past_price = sector_closes[-lookback]
                
                # Check for > 0 to avoid crash
                if past_price > 0:
                    mom = (current_price - past_price) / past_price
                    performance[sector] = mom

        # 4. Rank & Select Top 1
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_sectors) >= 1:
            top_pick = sorted_sectors[0][0]
            top_mom = sorted_sectors[0][1]

            # SAFETY FILTER: Momentum must be positive
            if top_mom > 0:
                final_order = None
                latest_day_data = relevant_data[-1]

                if top_pick in latest_day_data:
                    final_order = top_pick
                
                if final_order:
                    allocation_dict[final_order] = 1.0

        return TargetAllocation(allocation_dict)