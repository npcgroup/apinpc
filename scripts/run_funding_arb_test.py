import asyncio
import logging
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

from scripts.v2_funding_rate_arb import FundingRateArbitrage, FundingRateArbitrageConfig
from hummingbot.core.data_type.common import TradeType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_strategy():
    """Test the funding rate arbitrage strategy with real data"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Create configuration
        config = FundingRateArbitrageConfig(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            leverage=20,
            min_funding_rate_profitability=Decimal("0.001"),
            position_size_quote=Decimal("100"),
            profitability_to_take_profit=Decimal("0.01"),
            funding_rate_diff_stop_loss=Decimal("-0.001"),
            tokens={"BTC", "ETH", "SOL"}
        )
        
        # Initialize strategy
        strategy = FundingRateArbitrage(config=config)
        
        # Test market initialization
        logger.info("Testing market initialization...")
        strategy.initialize_markets()
        logger.info(f"Initialized markets: {strategy.markets}")
        
        # Test funding opportunity detection
        logger.info("\nTesting funding opportunity detection...")
        opportunities = await strategy.get_funding_opportunities()
        logger.info("\nTop Funding Opportunities:")
        logger.info(opportunities)
        
        # Test opportunity scoring
        if not opportunities.empty:
            for _, opp in opportunities.iterrows():
                score = strategy.calculate_opportunity_score(
                    opp['funding_diff'],
                    opp['predicted_diff'],
                    opp['avg_volume'],
                    opp['min_oi']
                )
                logger.info(f"\nOpportunity Score for {opp['token']}: {score}")
        
        # Test arbitrage execution simulation
        logger.info("\nTesting arbitrage execution simulation...")
        for token in config.tokens:
            combo = strategy.get_most_profitable_combination(token)
            if combo:
                logger.info(f"\nFound profitable combination for {token}:")
                logger.info(f"Connector 1: {combo[0]}")
                logger.info(f"Connector 2: {combo[1]}")
                logger.info(f"Side: {combo[2]}")
                logger.info(f"Rate Diff: {combo[3]}")
                
                # Simulate execution
                await strategy.execute_arbitrage(token, combo)
        
        # Display active arbitrages
        logger.info("\nActive Arbitrages:")
        logger.info(strategy.format_status())
        
    except Exception as e:
        logger.error(f"Error running strategy test: {e}")
        raise

def main():
    """Run the strategy test"""
    asyncio.run(test_strategy())

if __name__ == "__main__":
    main() 