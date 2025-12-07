from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # 1. Define the 11 Sectors
        self.sectors = [
            "XLK", "XLF", "XLV", "XLY", "XLP", 
            "XLE", "XLI", "XLB", "XLU", "XLRE", "XLC"
        ]
        
        # 2. Define Proxies (Use IYR if XLRE is missing)
        self.proxies = {"XLRE": "IYR"}
        
        # 3. Request data for all sectors + IYR
        self.tickers = self.sectors + ["IYR"]
        
        log("Strategy Initialized. Universe: " + str(self.tickers))

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
        if not data or "ohlcv" not in data or len(data["ohlcv"]) == 0:
            log("Waiting for data...")
            return TargetAllocation({})
        
        ohlcv_list = data["ohlcv"]
        allocation_dict = {}
        performance = {}
        lookback = 126  # 6 Months
        
        # 2. Loop through each SECTOR to build its specific history
        for sector in self.sectors:
            sector_closes = []
            
            # STITCHING LOGIC:
            # We look at every day in the history.
            # If the sector exists (e.g. XLRE), use it.
            # If not, check if the PROXY exists (e.g. IYR), use that.
            for day_data in ohlcv_list:
                if sector in day_data:
                    sector_closes.append(day_data[sector]["close"])
                elif sector in self.proxies and self.proxies[sector] in day_data:
                    # Proxy stitching (using IYR data as XLRE)
                    sector_closes.append(day_data[self.proxies[sector]]["close"])
            
            # 3. Calculate Momentum if we have enough stitched history
            if len(sector_closes) > lookback:
                current_price = sector_closes[-1]
                past_price = sector_closes[-lookback]
                
                # Check for zero division
                if past_price > 0:
                    momentum = (current_price - past_price) / past_price
                    performance[sector] = momentum
            else:
                # Log only once per backtest to avoid spam, or ignore
                pass

        # 4. Rank and Select Top 2
        # Sort descending by momentum
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_sectors) >= 2:
            top_picks = [sorted_sectors[0][0], sorted_sectors[1][0]]
            
            # LOGGING: Verify it's working
            # log(f"Date: {ohlcv_list[-1][self.tickers[0]]['date']} | Top: {top_picks}")

            # 5. Execution Logic
            # If we picked XLRE, but it doesn't exist today, we must buy IYR
            final_orders = []
            latest_day_data = ohlcv_list[-1]
            
            for pick in top_picks:
                if pick in latest_day_data:
                    final_orders.append(pick)
                elif pick in self.proxies and self.proxies[pick] in latest_day_data:
                    final_orders.append(self.proxies[pick])
            
            # Equal weight the valid orders
            if len(final_orders) > 0:
                weight = 1.0 / len(final_orders)
                for asset in final_orders:
                    allocation_dict[asset] = weight
        
        return TargetAllocation(allocation_dict)