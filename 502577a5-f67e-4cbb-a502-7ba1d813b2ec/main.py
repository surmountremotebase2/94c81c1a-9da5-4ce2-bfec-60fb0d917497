from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log

class TradingStrategy(Strategy):
    def __init__(self):
        # 1. Universe: "Classic 9" Sectors (Safe for long history)
        self.sectors = [
            "XLK", "XLF", "XLV", "XLY", "XLP", 
            "XLE", "XLI", "XLB", "XLU"
        ]
        self.tickers = self.sectors
        log("Strategy Loaded: Defensive Mode")

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
        # --- 1. CRITICAL DATA VALIDATION ---
        # If data is missing, empty, or A STRING (the cause of your crash), stop immediately.
        if not data or "ohlcv" not in data:
            return TargetAllocation({})
        
        ohlcv = data["ohlcv"]
        
        # Check if ohlcv is a list. If it is a string (e.g. "Error"), abort.
        if not isinstance(ohlcv, list):
            log(f"CRITICAL: Data is corrupted (Type: {type(ohlcv)}). Skipping day.")
            return TargetAllocation({})
            
        if len(ohlcv) < 30:
            return TargetAllocation({})

        # Slice to last 150 days to keep it fast
        relevant_data = ohlcv[-150:]
        
        allocation_dict = {}
        candidates = []
        lookback_mom = 126

        # --- 2. LOOP THROUGH SECTORS ---
        for sector in self.sectors:
            closes = []
            
            # Safe Extraction: Only pull data if it's a Dictionary
            for day in relevant_data:
                if isinstance(day, dict) and sector in day:
                    closes.append(float(day[sector]["close"]))
            
            # Ensure we have enough history for this specific sector
            if len(closes) > lookback_mom:
                current_price = closes[-1]
                past_price = closes[-lookback_mom]
                
                # Check Momentum
                if past_price > 0:
                    momentum = (current_price - past_price) / past_price
                    
                    if momentum > 0:
                        # --- 3. MANUAL RSI CALCULATION (10-Day) ---
                        # We do this here to avoid the "Import RSI" crash
                        rsi_period = 10
                        if len(closes) > rsi_period + 1:
                            # Get last 11 days
                            recent = closes[-(rsi_period+1):]
                            gains = []
                            losses = []
                            
                            for i in range(1, len(recent)):
                                change = recent[i] - recent[i-1]
                                if change > 0:
                                    gains.append(change)
                                else:
                                    losses.append(abs(change))
                            
                            # Simple average (Wilder's Smoothing not strictly needed for ranking)
                            avg_gain = sum(gains) / rsi_period
                            avg_loss = sum(losses) / rsi_period
                            
                            if avg_loss == 0:
                                rsi = 100
                            else:
                                rs = avg_gain / avg_loss
                                rsi = 100 - (100 / (1 + rs))
                            
                            candidates.append((sector, rsi))

        # --- 4. SELECTION ---
        # Sort by Lowest RSI
        candidates.sort(key=lambda x: x[1])
        
        if len(candidates) > 0:
            best_sector = candidates[0][0]
            # log(f"Winner: {best_sector} | RSI: {candidates[0][1]:.2f}")
            
            # Double check existence in latest data
            if isinstance(relevant_data[-1], dict) and best_sector in relevant_data[-1]:
                allocation_dict[best_sector] = 1.0

        return TargetAllocation(allocation_dict)