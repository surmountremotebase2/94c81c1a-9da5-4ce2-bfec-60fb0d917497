from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
# IMPORT THE BUILT-IN INDICATORS (This is 100x faster than manual loops)
from surmount.technical_indicators import RSI

class TradingStrategy(Strategy):
    def __init__(self):
        # Classic 9 Sectors (Safe for long history)
        self.sectors = [
            "XLK", "XLF", "XLV", "XLY", "XLP", 
            "XLE", "XLI", "XLB", "XLU"
        ]
        self.tickers = self.sectors
        log("Strategy Loaded: Fast Version")

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
        candidates = []
        
        # Trend Lookback (Momentum)
        lookback_mom = 126 

        for sector in self.sectors:
            # 1. Get the RSI using the built-in function (Fast!)
            # RSI(ohlcv_data, ticker, length)
            rsi_data = RSI(data["ohlcv"], sector, 10)
            
            # Check if we have enough data for RSI
            if not rsi_data or len(rsi_data) == 0:
                continue
            
            current_rsi = rsi_data[-1]

            # 2. Check Momentum (Manual check is fine here, it's just 1 subtraction)
            # We need to access the raw OHLCV for price history
            if sector in data["ohlcv"]:
                ticker_data = data["ohlcv"][sector]
                
                if len(ticker_data) > lookback_mom:
                    current_price = ticker_data[-1]["close"]
                    past_price = ticker_data[-lookback_mom]["close"]
                    
                    # Avoid division by zero
                    if past_price > 0:
                        momentum = (current_price - past_price) / past_price
                        
                        # 3. FILTER: Positive Trend + Valid RSI
                        if momentum > 0:
                            candidates.append((sector, current_rsi))

        # --- SELECTION ---
        # Sort by Lowest RSI
        candidates.sort(key=lambda x: x[1])
        
        if len(candidates) > 0:
            # Pick the Winner
            best_sector = candidates[0][0]
            
            # log(f"Buying {best_sector} | RSI: {candidates[0][1]}")
            allocation_dict[best_sector] = 1.0

        return TargetAllocation(allocation_dict)