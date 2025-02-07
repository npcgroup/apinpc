import os
from decimal import Decimal
from typing import Dict, List, Optional, Union, Set
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging
from pydantic import Field, validator
from hummingbot.strategy.strategy_v2_base import StrategyV2ConfigBase

from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, TradeType
from hummingbot.core.event.events import FundingPaymentCompletedEvent, BuyOrderCompleted, SellOrderCompleted
from hummingbot.connector.connector_base import ConnectorBase

logger = logging.getLogger(__name__)

class FundingEnhancedArbitrageConfig(StrategyV2ConfigBase):
    """Configuration parameters for the FundingEnhancedArbitrage strategy"""
    
    script_file_name: str = Field(default_factory=lambda: os.path.basename(__file__))
    
    # Supabase configuration
    supabase_url: str = Field(
        default="https://llanxjeohlxpnndhqbdp.supabase.co",
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter your Supabase URL: ",
            prompt_on_new=True
        )
    )
    
    supabase_key: str = Field(
        default="",
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter your Supabase API key: ",
            prompt_on_new=True
        )
    )
    
    # Market configuration
    connectors: Set[str] = Field(
        default={"hyperliquid_perpetual_testnet", "binance_perpetual_testnet"},
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the connectors separated by commas (e.g. hyperliquid_perpetual_testnet,binance_perpetual_testnet): ",
            prompt_on_new=True
        )
    )
    
    tokens: Set[str] = Field(
        default={"BTC", "ETH", "SOL"},
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the trading tokens separated by commas (e.g. BTC,ETH,SOL): ",
            prompt_on_new=True
        )
    )
    
    # Trading parameters
    leverage: int = Field(
        default=20,
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the leverage to use (e.g. 20): ",
            prompt_on_new=True
        )
    )
    
    position_size_quote: Decimal = Field(
        default=Decimal("100"),
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the position size in quote currency (e.g. 100): ",
            prompt_on_new=True
        )
    )
    
    min_funding_rate_profitability: Decimal = Field(
        default=Decimal("0.001"),
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the minimum funding rate profitability (e.g. 0.001 for 0.1%): ",
            prompt_on_new=True
        )
    )
    
    profitability_to_take_profit: Decimal = Field(
        default=Decimal("0.01"),
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the profitability target for take profit (e.g. 0.01 for 1%): ",
            prompt_on_new=True
        )
    )
    
    funding_rate_diff_stop_loss: Decimal = Field(
        default=Decimal("-0.001"),
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the funding rate difference for stop loss (e.g. -0.001 for -0.1%): ",
            prompt_on_new=True
        )
    )
    
    update_interval: int = Field(
        default=300,
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter the update interval in seconds (e.g. 300 for 5 minutes): ",
            prompt_on_new=True
        )
    )
    
    @validator("connectors", "tokens", pre=True)
    def validate_comma_separated_values(cls, v):
        """Convert comma-separated string to set if needed"""
        if isinstance(v, str):
            return {item.strip() for item in v.split(",")}
        return v
    
    @validator("leverage")
    def validate_leverage(cls, v):
        """Validate leverage is within reasonable bounds"""
        if v > 100:
            raise ValueError("Leverage cannot exceed 100x")
        return v
    
    @validator("position_size_quote")
    def validate_position_size(cls, v):
        """Validate position size is reasonable"""
        if v > Decimal("10000"):
            raise ValueError("Position size cannot exceed 10000 quote currency units")
        return v

class FundingEnhancedArbitrage(ScriptStrategyBase):
    """
    Enhanced arbitrage strategy that leverages predicted funding rates from Supabase
    and real-time market data to execute funding arbitrage between Hyperliquid and Binance.
    """
    
    markets = {  # This needs to be a class variable, not an instance variable
        "hyperliquid_perpetual_testnet": ["BTC-USD", "ETH-USD", "SOL-USD"],
        "binance_perpetual_testnet": ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    }
    
    quote_markets_map = {
        "hyperliquid_perpetual_testnet": "USD",
        "binance_perpetual_testnet": "USDT"
    }
    
    funding_payment_interval_map = {
        "binance_perpetual_testnet": 60 * 60 * 8,      # 8 hours
        "hyperliquid_perpetual_testnet": 60 * 60 * 1   # 1 hour
    }

    def __init__(self, config: FundingEnhancedArbitrageConfig):
        super().__init__()
        
        # Initialize Supabase client
        from supabase import create_client
        self.supabase = create_client(config.supabase_url, config.supabase_key)
        
        # Strategy parameters from config
        self.config = config
        self.connectors = config.connectors
        self.tokens = config.tokens
        self.leverage = config.leverage
        self.min_funding_rate_profitability = config.min_funding_rate_profitability
        self.position_size_quote = config.position_size_quote
        self.profitability_to_take_profit = config.profitability_to_take_profit
        self.funding_rate_diff_stop_loss = config.funding_rate_diff_stop_loss
        self.update_interval = config.update_interval
        
        # State management
        self.active_funding_arbitrages = {}
        self.stopped_funding_arbitrages = {token: [] for token in self.tokens}
        self.funding_payments_collected = {}
        self.last_funding_update = {}

    def on_start(self):
        """Initialize strategy settings and start background tasks"""
        self.apply_initial_settings()
        self.start_background_tasks()
        logger.info("Strategy started - initializing markets and parameters...")

    def apply_initial_settings(self):
        """Apply initial leverage and position mode settings"""
        for connector_name, connector in self.connectors.items():
            if hasattr(connector, "set_leverage"):
                position_mode = PositionMode.ONEWAY if connector_name == "hyperliquid_perpetual_testnet" else PositionMode.HEDGE
                connector.set_position_mode(position_mode)
                for token in self.tokens:
                    trading_pair = self.get_trading_pair(token, connector_name)
                    connector.set_leverage(trading_pair, self.leverage)

    def get_trading_pair(self, token: str, connector: str) -> str:
        """Get the correct trading pair format for each connector"""
        quote = self.quote_markets_map.get(connector, "USDT")
        return f"{token}-{quote}"

    async def fetch_funding_rates(self):
        """Fetch current and predicted funding rates from Supabase"""
        try:
            # Get latest opportunities from our new table
            response = self.supabase.table('funding_arbitrage_opportunities').select(
                'coin',
                'hyperliquid_rate',
                'counterparty',
                'counterparty_rate',
                'spread',
                'timestamp'
            ).order('timestamp.desc').limit(10).execute()
            
            if not response.data:
                logger.warning("No funding rate opportunities found in Supabase")
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            return pd.DataFrame()

    def get_normalized_funding_rate(self, funding_data: pd.DataFrame, connector: str) -> Decimal:
        """Get normalized funding rate for a connector"""
        try:
            exchange_name = 'hyperliquid_testnet' if 'hyperliquid' in connector else 'binance_testnet'
            connector_data = funding_data[funding_data['exchange'] == exchange_name]
            
            if connector_data.empty:
                return Decimal("0")
            
            current_rate = Decimal(str(connector_data['current_funding_rate'].iloc[0]))
            predicted_rate = Decimal(str(connector_data['predicted_funding_rate'].iloc[0]))
            
            # Weight current and predicted rates
            normalized_rate = (current_rate * Decimal("0.7")) + (predicted_rate * Decimal("0.3"))
            return normalized_rate
            
        except Exception as e:
            logger.error(f"Error normalizing funding rate: {e}")
            return Decimal("0")

    def get_most_profitable_combination(self, token: str) -> tuple:
        """Find the most profitable funding rate arbitrage opportunity"""
        try:
            funding_rates = self.fetch_funding_rates()
            if funding_rates.empty:
                return None
            
            token_rates = funding_rates[funding_rates['symbol'].str.startswith(token)]
            
            max_profit = Decimal("-inf")
            best_combo = None
            
            for c1 in self.connectors:
                for c2 in self.connectors:
                    if c1 >= c2:
                        continue
                        
                    rate1 = self.get_normalized_funding_rate(token_rates, c1)
                    rate2 = self.get_normalized_funding_rate(token_rates, c2)
                    
                    # Calculate rate difference and determine direction
                    rate_diff = rate1 - rate2
                    if abs(rate_diff) > max_profit:
                        max_profit = abs(rate_diff)
                        side = TradeType.BUY if rate_diff < 0 else TradeType.SELL
                        best_combo = (c1, c2, side, rate_diff)
            
            return best_combo
            
        except Exception as e:
            logger.error(f"Error finding profitable combination: {e}")
            return None

    async def execute_arbitrage(self, token: str, combo: tuple):
        """Execute the arbitrage trade"""
        if not combo:
            return
            
        connector1, connector2, side, rate_diff = combo
        
        if abs(rate_diff) < self.min_funding_rate_profitability:
            return
            
        try:
            # Calculate position sizes
            price1 = self.get_price(connector1, self.get_trading_pair(token, connector1))
            price2 = self.get_price(connector2, self.get_trading_pair(token, connector2))
            
            size1 = self.position_size_quote / price1
            size2 = self.position_size_quote / price2
            
            # Place orders
            order1 = await self.place_order(
                connector=connector1,
                trading_pair=self.get_trading_pair(token, connector1),
                order_type=OrderType.MARKET,
                side=side,
                amount=size1,
                price=price1
            )
            
            order2 = await self.place_order(
                connector=connector2,
                trading_pair=self.get_trading_pair(token, connector2),
                order_type=OrderType.MARKET,
                side=TradeType.BUY if side == TradeType.SELL else TradeType.SELL,
                amount=size2,
                price=price2
            )
            
            # Record the arbitrage
            self.active_funding_arbitrages[token] = {
                "connector_1": connector1,
                "connector_2": connector2,
                "side": side,
                "entry_time": datetime.now(),
                "funding_payments": Decimal("0"),
                "orders": [order1, order2]
            }
            
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")

    def on_funding_payment_completed(self, event: FundingPaymentCompletedEvent):
        """Handle funding payment events"""
        if event.trading_pair not in self.active_funding_arbitrages:
            return
            
        arb_info = self.active_funding_arbitrages[event.trading_pair]
        arb_info["funding_payments"] += event.funding_payment
        
        # Check if take profit reached
        if arb_info["funding_payments"] >= self.profitability_to_take_profit:
            asyncio.create_task(self.close_arbitrage(event.trading_pair))

    async def monitor_positions(self):
        """Monitor active positions and check for exit conditions"""
        while True:
            try:
                for token, arb_info in self.active_funding_arbitrages.items():
                    funding_rates = await self.fetch_funding_rates()
                    current_diff = self.calculate_funding_rate_diff(
                        funding_rates,
                        token,
                        arb_info["connector_1"],
                        arb_info["connector_2"]
                    )
                    
                    if current_diff <= self.funding_rate_diff_stop_loss:
                        await self.close_arbitrage(token)
                        
            except Exception as e:
                logger.error(f"Error monitoring positions: {e}")
                
            await asyncio.sleep(self.update_interval)

    def format_status(self) -> str:
        """Format status message for display"""
        lines = []
        lines.append("\n")
        lines.append("Funding Enhanced Arbitrage Status")
        lines.append(f"Active Arbitrages: {len(self.active_funding_arbitrages)}")
        
        for token, arb_info in self.active_funding_arbitrages.items():
            lines.append(f"\nToken: {token}")
            lines.append(f"Direction: Long {arb_info['connector_1']}, Short {arb_info['connector_2']}")
            lines.append(f"Funding Collected: {arb_info['funding_payments']:.4f}")
            lines.append(f"Time Active: {datetime.now() - arb_info['entry_time']}")
        
        return "\n".join(lines)

    def start_background_tasks(self):
        """Start background monitoring tasks"""
        self.task_monitor = asyncio.create_task(self.monitor_positions())
        logger.info("Started background monitoring tasks")

    async def close_arbitrage(self, token: str):
        """Close an active arbitrage position"""
        if token not in self.active_funding_arbitrages:
            return
            
        arb_info = self.active_funding_arbitrages[token]
        try:
            # Close positions in both markets
            for connector, order in zip([arb_info["connector_1"], arb_info["connector_2"]], arb_info["orders"]):
                close_side = TradeType.SELL if order.side == TradeType.BUY else TradeType.BUY
                await self.place_order(
                    connector=connector,
                    trading_pair=self.get_trading_pair(token, connector),
                    order_type=OrderType.MARKET,
                    side=close_side,
                    amount=order.amount,
                    price=self.get_price(connector, self.get_trading_pair(token, connector))
                )
            
            # Record the closed position
            self.stopped_funding_arbitrages[token].append({
                "entry_time": arb_info["entry_time"],
                "exit_time": datetime.now(),
                "funding_collected": arb_info["funding_payments"]
            })
            
            del self.active_funding_arbitrages[token]
            logger.info(f"Successfully closed arbitrage position for {token}")
            
        except Exception as e:
            logger.error(f"Error closing arbitrage position: {e}")

def main():
    # Example configuration
    config = FundingEnhancedArbitrageConfig(
        supabase_key="your_key_here",
        leverage=20,
        position_size_quote=Decimal("100"),
        min_funding_rate_profitability=Decimal("0.001"),
        tokens={"BTC", "ETH", "SOL"}
    )
    strategy = FundingEnhancedArbitrage(config=config)
    strategy.run()

if __name__ == "__main__":
    main()