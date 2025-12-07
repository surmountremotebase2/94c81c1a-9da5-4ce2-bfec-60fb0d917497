from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # 1. Use the "Classic 9" to ensure long history (Back to 2000)
        # We exclude XLC and XLRE to prevent "Failed to Fetch" errors
        self.sectors = [
            "XLK", "XLF", "XLV", "XLY", "XLP", 
            "XLE", "XLI", "XLB", "XLU"
        ]
        self.tickers = self.sectors
        log("Strategy Loaded: Buy Dip in Uptrend (RSI 10)")

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
        # --- SAFETY & DATA CHECKS ---
        if not data or "ohlcv" not in data:
            return TargetAllocation({})
        
        ohlcv_full = data["ohlcv"]
        if len(ohlcv_full) < 30: # Need enough data for RSI
            return TargetAllocation({})

        # Optimization: Slice data to last 200 days for speed
        lookback_mom = 126
        buffer = 30
        if len(ohlcv_full) > (lookback_mom + buffer):
            relevant_data = ohlcv_full[-(lookback_mom + buffer):]
        else:
            relevant_data = ohlcv_full

        allocation_dict = {}
        candidates = []

        # --- LOOP THROUGH SECTORS ---
        for sector in self.sectors:
            closes = []
            
            # Extract closing prices
            for day in relevant_data:
                if sector in day:
                    closes.append(float(day[sector]["close"]))
            
            # We need enough data for Momentum (126) and RSI (10)
            if len(closes) >= lookback_mom:
                current_price = closes[-1]
                past_price = closes[-lookback_mom]
                
                # 1. MOMENTUM CHECK
                # Only consider sectors that are higher than they were 6 months ago
                momentum = (current_price - past_price) / past_price
                
                if momentum > 0:
                    # 2. RSI CALCULATION (10-Day)
                    # We calculate RSI manually here to ensure stability
                    rsi_period = 10
                    delta = []
                    
                    # Get price changes for the last 10 days
                    recent_closes = closes[-(rsi_period+1):]
                    for i in range(1, len(recent_closes)):
                        change = recent_closes[i] - recent_closes[i-1]
                        delta.append(change)
                    
                    # Separate Gains and Losses
                    gains = [x for x in delta if x > 0]
                    losses = [abs(x) for x in delta if x < 0]
                    
                    # Calculate Averages (Simple Average for robustness in small samples)
                    avg_gain = sum(gains) / rsi_period
                    avg_loss = sum(losses) / rsi_period
                    
                    if avg_loss == 0:
                        rsi = 100
                    else:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                    
                    # Store as candidate: (Ticker, RSI)
                    candidates.append((sector, rsi))

        # --- SELECTION ---
        # Sort candidates by RSI (Ascending) -> Lowest RSI first
        candidates.sort(key=lambda x: x[1])
        
        if len(candidates) > 0:
            best_sector = candidates[0][0]
            best_rsi = candidates[0][1]
            
            # log(f"Buying {best_sector} | RSI(10): {best_rsi:.2f} | Momentum > 0")
            
            # Check if tradeable today
            latest_data = relevant_data[-1]
            if best_sector in latest_data:
                allocation_dict[best_sector] = 1.0
        else:
            # If candidates is empty, it means NO sectors have positive momentum.
            # Strategy goes to Cash (Safety).
            pass # allocation_dict remains empty

        return TargetAllocation(allocation_dict)