# 4. Rank and Select Top 1 (Winner Takes All)
        # Sort descending by momentum
        sorted_sectors = sorted(performance.items(), key=lambda x: x[1], reverse=True)
        
        # LOGIC CHANGE: Check for at least 1 valid sector, not 2
        if len(sorted_sectors) >= 1:
            # Select only the absolute winner
            top_pick = sorted_sectors[0][0]
            
            # 5. Execution Logic (Proxy Check)
            final_order = None
            latest_day_data = ohlcv_list[-1]
            
            # Check if the winner is tradeable today
            if top_pick in latest_day_data:
                final_order = top_pick
            elif top_pick in self.proxies and self.proxies[top_pick] in latest_day_data:
                final_order = self.proxies[top_pick]
            
            # Execute 100% allocation if valid
            if final_order:
                log(f"Top Sector: {top_pick} -> Buying 100% {final_order}")
                allocation_dict[final_order] = 1.0
            else:
                log(f"Top pick {top_pick} is not tradeable today. Staying Cash.")
        
        return TargetAllocation(allocation_dict)