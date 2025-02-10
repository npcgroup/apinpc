import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from scripts.advanced_funding_analyzer import AdvancedFundingAnalyzer

def main():
    try:
        analyzer = AdvancedFundingAnalyzer()
        df = analyzer.fetch_data()
        
        if df.empty:
            raise Exception("No data available")

        # Calculate statistics
        stats = analyzer.calculate_stats(df)
        
        # Generate visualizations data
        viz_data = analyzer.create_visualizations(df)
        
        # Prepare response
        response = {
            "stats": {
                "total_markets": stats["total_markets"],
                "binance_markets": stats["binance_markets"],
                "hl_markets": stats["hl_markets"],
                "hourly_rate": stats["hourly_rate"],
                "eight_hour_rate": stats["eight_hour_rate"],
                "daily_rate": stats["daily_rate"]
            },
            "opportunities": viz_data.get("top_opportunities", []),
            "analysis": {
                "distribution": viz_data.get("funding_distribution", {}),
                "heatmap": viz_data.get("funding_heatmap", {}),
                "exchange_comparison": viz_data.get("exchange_comparison", {})
            },
            "detailed": df.to_dict(orient="records")
        }
        
        # Print JSON response for Node.js to capture
        print(json.dumps(response))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main() 