import unittest
from unittest.mock import Mock, patch
import asyncio
from decimal import Decimal
import pandas as pd
from datetime import datetime, timedelta

from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, TradeType
from hummingbot.core.event.events import FundingPaymentCompletedEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase

class TestFundingRateArbitrage(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = Mock()
        self.config.leverage = 20
        self.config.min_funding_rate_profitability = Decimal("0.001")
        self.config.position_size_quote = Decimal("100")
        self.config.profitability_to_take_profit = Decimal("0.01")
        self.config.funding_rate_diff_stop_loss = Decimal("-0.001")
        self.config.tokens = {"BTC", "ETH", "SOL"}
        self.config.supabase_url = "mock_url"
        self.config.supabase_key = "mock_key"

        # Create mock connectors
        self.hyperliquid_connector = Mock()
        self.binance_connector = Mock()
        
        self.connectors = {
            "hyperliquid_perpetual_testnet": self.hyperliquid_connector,
            "binance_perpetual_testnet": self.binance_connector
        }

        # Initialize strategy
        with patch('supabase.create_client'):
            from scripts.v2_funding_rate_arb import FundingRateArbitrage
            self.strategy = FundingRateArbitrage(
                connectors=self.connectors,
                config=self.config
            )

    def test_initialize_markets(self):
        """Test market initialization"""
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [
            {"symbol": "BTC-USD"},
            {"symbol": "ETH-USD"},
            {"symbol": "SOL-USD"}
        ]
        
        self.strategy.supabase.table().select().execute = Mock(return_value=mock_response)
        
        # Run initialization
        self.strategy.initialize_markets()
        
        # Verify markets were set correctly
        expected_markets = {
            "hyperliquid_perpetual_testnet": ["BTC-USD", "ETH-USD", "SOL-USD"],
            "binance_perpetual_testnet": ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
        }
        self.assertEqual(self.strategy.markets, expected_markets)

    @patch('scripts.v2_funding_rate_arb.FundingRateArbitrage.get_funding_opportunities')
    def test_get_most_profitable_combination(self, mock_get_opportunities):
        """Test finding the most profitable funding rate combination"""
        # Mock funding opportunities data
        mock_opportunities = pd.DataFrame({
            'token': ['BTC'],
            'connector_1': ['hyperliquid_perpetual_testnet'],
            'connector_2': ['binance_perpetual_testnet'],
            'funding_diff': [0.002],
            'predicted_diff': [0.0025],
            'avg_volume': [1000000],
            'min_oi': [2000000],
            'opportunity_score': [0.8]
        })
        mock_get_opportunities.return_value = mock_opportunities

        # Test getting profitable combination
        result = self.strategy.get_most_profitable_combination("BTC")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 4)  # Should return (connector1, connector2, side, rate_diff)

    def test_calculate_opportunity_score(self):
        """Test opportunity score calculation"""
        score = self.strategy.calculate_opportunity_score(
            funding_diff=0.002,
            predicted_diff=0.0025,
            avg_volume=1000000,
            min_oi=2000000
        )
        
        self.assertGreater(score, 0)
        self.assertIsInstance(score, float)

    def test_on_funding_payment_completed(self):
        """Test handling of funding payment events"""
        # Create mock funding payment event
        event = FundingPaymentCompletedEvent(
            timestamp=datetime.now().timestamp(),
            trading_pair="BTC-USDT",
            funding_rate=0.001,
            funding_payment=Decimal("0.1")
        )
        
        # Setup active arbitrage
        self.strategy.active_funding_arbitrages = {
            "BTC-USDT": {
                "connector_1": "hyperliquid_perpetual_testnet",
                "connector_2": "binance_perpetual_testnet",
                "funding_payments": []
            }
        }
        
        # Test event handling
        self.strategy.on_funding_payment_completed(event)
        
        # Verify payment was recorded
        self.assertEqual(
            len(self.strategy.active_funding_arbitrages["BTC-USDT"]["funding_payments"]),
            1
        )

    async def test_execute_arbitrage(self):
        """Test arbitrage execution"""
        # Mock market data
        self.strategy.get_price = Mock(return_value=Decimal("50000"))
        
        # Create test combination
        combo = (
            "hyperliquid_perpetual_testnet",
            "binance_perpetual_testnet",
            TradeType.BUY,
            Decimal("0.002")
        )
        
        # Mock order placement
        self.strategy.place_order = Mock(return_value=Mock())
        
        # Execute arbitrage
        await self.strategy.execute_arbitrage("BTC", combo)
        
        # Verify orders were placed
        self.assertEqual(self.strategy.place_order.call_count, 2)
        
        # Verify arbitrage was recorded
        self.assertIn("BTC", self.strategy.active_funding_arbitrages)

def main():
    unittest.main()

if __name__ == "__main__":
    unittest.main() 