from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # 1. Define the 11 Select Sector SPDR ETFs
        self.sectors = [
            "XLK", # Technology
            "XLF", # Financials
            "XLV", # Health Care
            "XLY", # Consumer Discretionary
            "XLP", # Consumer Staples
            "XLE", # Energy
            "XLI", # Industrials
            "XLB", # Materials
            "XLU", # Utilities
            "XLRE", # Real Estate
            "XLC"  # Communication Services
        ]
        
        # Define Proxy: Use IYR (Real Estate) to simulate XLRE before 2015
        self.proxies = {"XLRE": "IYR"}
        
        # Request data for all sectors + the proxy
        self.tickers = self.sectors + ["IYR"]
        
        log("Strategy Loaded: Top 1 Sector Momentum")

    @property
    def interval(self):
        # Run this logic once daily
        return "1day"

    @property
    def assets(self):
        # Load data for these tickers
        return self.tickers

    @property
    def data(self):
        # No extra external data needed
        return []

    def run(self, data):
        # --- 1. SAFETY CHECKS ---
        # If no data is present, return empty (Cash)
        if not data or "ohlcv" not in data:
            return TargetAllocation({})
        
        ohlcv_full = data["ohlcv"]
        if len(ohlcv_full) < 10:
            return TargetAllocation({})

        # --- 2. DATA OPTIMIZATION ---
        # Only process the last 200 days to prevent timeouts ("Line 621 Error")
        lookback = 126
        buffer = 20
        if len(ohlcv_full) > (lookback + buffer):
            relevant_data = ohlcv_full[-(lookback + buffer):]
        else:
            relevant_data = ohlcv_full

        allocation_dict = {}
        performance = {}

        # --- 3. CALCULATE MOMENTUM ---
        for sector in self.sectors:
            sector_closes = []
            
            # Stitching Logic: Handle XLRE / IYR proxy
            for day_data in relevant_data:
                # If the real sector exists, use it
                if sector in day_data:
                    val = day_data[sector]["close"]
                    sector_closes.append(float(val))
                # If not, check if we have a proxy for it (e.g. IYR)
                elif sector in self.proxies and self.proxies[sector] in day_data:
                    val = day_data[self.proxies[sector]]["close"]
                    sector_closes.append(float(val))
            
            # Calculate Return if we have enough history
            if len(sector_closes) >= lookback:
                current_price = sector_closes[-1]
                past_price = sector_closes[-lookback]
                
                if past_price > 0:
                    mom = (current_price - past_price) / past_price
                    performance[sector] = mom

        # --- 4. RANKING & SELECTION ---
        # Sort by Momentum (Highest to Lowest)
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)

        # Select Top 1
        if len(sorted_sectors) >= 1:
            top_pick = sorted_sectors[0][0]  # The Ticker Name (e.g. "XLK")
            top_mom = sorted_sectors[0][1]   # The Score (e.g. 0.15)

            # SAFETY FILTER: Only buy if the sector is actually going UP (> 0%)
            # If the best sector is down -5%, we stay in Cash.
            if top_mom > 0:
                final_order = None
                latest_day_data = relevant_data[-1]

                # Execution Check: Ensure the asset is tradeable TODAY
                if top_pick in latest_day_data:
                    final_order = top_pick
                elif top_pick in self.proxies and self.proxies[top_pick] in latest_day_data:
                    final_order = self.proxies[top_pick]
                
                # Assign 100% Allocation
                if final_order:
                    # log(f"Buying {final_order} (Momentum: {top_mom:.2%})")
                    allocation_dict[final_order] = 1.0

        # --- 5. EXECUTE ---
        return TargetAllocation(allocation_dict)