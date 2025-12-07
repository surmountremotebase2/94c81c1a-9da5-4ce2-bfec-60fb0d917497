from surmount.base_class import Strategy, TargetAllocation
from surmount.logging import log
from surmount.data import Asset

class TradingStrategy(Strategy):
    def __init__(self):
        # Define the 11 Select Sector SPDR ETFs
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
        self.tickers = self.sectors

    @property
    def interval(self):
        # run this check once a day
        return "1day"

    @property
    def assets(self):
        return self.tickers

    @property
    def data(self):
        # Request OHLCV data for all sectors
        return []

    def run(self, data):
        # 1. Initialize an empty dictionary for our allocation
        allocation_dict = {}
        
        # 2. Define our "Momentum" Lookback (e.g., 126 trading days = ~6 months)
        lookback = 126
        
        # Dictionary to store performance for each sector
        performance = {}

        # 3. Loop through each sector to calculate returns
        for ticker in self.tickers:
            ohlcv = data["ohlcv"]
            
            # Check if we have enough data points for this ticker
            if len(ohlcv) > 0 and len(ohlcv) >= lookback:
                # Get the data for this specific ticker
                # The data structure is usually a list of dicts per ticker
                # We need to ensure we access the specific ticker's history
                # Note: In Surmount, data['ohlcv'] often comes as a list of all requested assets. 
                # We filter for the specific ticker's closing prices.
                
                # Extract closing prices for this specific ticker
                closes = [x[ticker]["close"] for x in ohlcv if ticker in x]
                
                if len(closes) >= lookback:
                    current_price = closes[-1]
                    past_price = closes[-lookback]
                    
                    # Calculate simple return (Momentum)
                    roc = (current_price - past_price) / past_price
                    performance[ticker] = roc
            else:
                # Not enough data? Skip it.
                continue

        # 4. Sort the sectors by performance (Highest to Lowest)
        # sorted_sectors will be a list of tuples: [('XLK', 0.15), ('XLE', 0.12), ...]
        sorted_sectors = sorted(performance.items(), key=lambda item: item[1], reverse=True)

        # 5. Select the Top 2
        if len(sorted_sectors) >= 2:
            top_picks = [sorted_sectors[0][0], sorted_sectors[1][0]]
            
            log(f"Top 2 Momentum Sectors: {top_picks}")
            
            # 6. Assign 50% allocation to each
            for ticker in top_picks:
                allocation_dict[ticker] = 0.5
        else:
            # Fallback: If not enough data, hold cash (empty allocation)
            log("Not enough data to calculate momentum.")

        # 7. Return the target allocation
        # Surmount will automatically buy/sell to match these %s
        return TargetAllocation(allocation_dict)