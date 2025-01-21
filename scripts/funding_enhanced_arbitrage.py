from decimal import Decimal
import logging
from typing import Dict, List, Optional, Union
import asyncio
import pandas as pd
import time
from datetime import datetime, timedelta

from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.core.event.events import BuyOrderCompleted, SellOrderCompleted

from funding_data.supabase_client import SupabaseFundingRateClient
from funding_data.strategy_adjustments import StrategyAdjuster, StrategyParameters

logger = logging.getLogger(__name__)

class FundingEnhancedArbitrage(ScriptStrategyBase):
    """
    A Hummingbot strategy that uses funding rate data to optimize arbitrage between
    Hyperliquid and Binance perpetual markets.
    """
    
    markets = {
        "hyperliquid_perpetual": ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
        "binance_perpetual": ["BTC-USDT", "ETH-USDT", "SOL-USDT"]
    }

    def __init__(self,
                 supabase_url: str,
                 supabase_key: str,
                 min_profitability: Decimal = Decimal("0.002"),  # 0.2% minimum profitability
                 max_position_size: Decimal = Decimal("0.1"),    # 10% of available balance
                 update_interval: int = 300,
                 max_leverage: Decimal = Decimal("3.0"),     # Add maximum leverage
                 stop_loss: Decimal = Decimal("0.02"),       # 2% stop loss
                 take_profit: Decimal = Decimal("0.01"),     # 1% take profit
                 max_active_positions: int = 3):             # Maximum concurrent positions
        
        super().__init__()
        
        # Initialize components
        self.funding_client = SupabaseFundingRateClient(supabase_url, supabase_key)
        self.strategy_adjuster = StrategyAdjuster()
        
        # Strategy parameters
        self.min_profitability = min_profitability
        self.max_position_size = max_position_size
        self.update_interval = update_interval
        self.max_leverage = max_leverage
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.max_active_positions = max_active_positions
        
        # State management
        self.current_parameters: Dict[str, StrategyParameters] = {}
        self.active_orders: Dict[str, List] = {}
        self.positions: Dict[str, Dict] = {}
        
        # Performance tracking
        self.total_pnl = Decimal("0")
        self.trade_count = 0
        self.trade_history: List[Dict] = []
        self.last_funding_payment: Dict[str, datetime] = {}

    def on_start(self):
        """Called when the strategy starts."""
        self.start_background_tasks()
        logger.info("Strategy started - initializing markets and parameters...")

    def on_stop(self):
        """Called when the strategy stops."""
        self.close_all_positions()
        logger.info("Strategy stopped - closing positions and canceling orders...")

    def start_background_tasks(self):
        """Start background tasks for data updates and position monitoring."""
        self.create_background_task(self.update_parameters_loop())
        self.create_background_task(self.monitor_positions_loop())

    async def update_parameters_loop(self):
        """Periodically update strategy parameters based on funding rates."""
        while True:
            try:
                funding_data = self.funding_client.fetch_latest_funding_rates()
                
                for market in self.markets["hyperliquid_perpetual"]:
                    params = self.strategy_adjuster.calculate_parameters(
                        symbol=market,
                        funding_data=funding_data
                    )
                    if params:
                        self.current_parameters[market] = params
                        logger.info(f"Updated parameters for {market}: {params}")
                
            except Exception as e:
                logger.error(f"Error updating parameters: {e}")
            
            await asyncio.sleep(self.update_interval)

    async def monitor_positions_loop(self):
        """Monitor and manage open positions."""
        while True:
            try:
                for market in self.markets["hyperliquid_perpetual"]:
                    await self.check_and_close_positions(market)
            except Exception as e:
                logger.error(f"Error monitoring positions: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    def on_tick(self):
        """Called on each clock tick."""
        try:
            for market in self.markets["hyperliquid_perpetual"]:
                self.check_and_execute_arbitrage(market)
        except Exception as e:
            logger.error(f"Error in tick processing: {e}")

    def check_and_execute_arbitrage(self, market: str):
        """Check for and execute arbitrage opportunities."""
        params = self.current_parameters.get(market)
        if not params:
            return

        try:
            # Get market prices
            hyper_bid = self.get_price("hyperliquid_perpetual", market, True)
            hyper_ask = self.get_price("hyperliquid_perpetual", market, False)
            binance_bid = self.get_price("binance_perpetual", market, True)
            binance_ask = self.get_price("binance_perpetual", market, False)

            # Calculate spreads
            hyper_binance_spread = (binance_bid - hyper_ask) / hyper_ask
            binance_hyper_spread = (hyper_bid - binance_ask) / binance_ask

            # Execute trades if profitable
            if hyper_binance_spread > self.min_profitability and params.direction in ['both', 'long']:
                self.execute_arbitrage(
                    buy_exchange="hyperliquid_perpetual",
                    sell_exchange="binance_perpetual",
                    market=market,
                    spread=hyper_binance_spread,
                    params=params
                )

            elif binance_hyper_spread > self.min_profitability and params.direction in ['both', 'short']:
                self.execute_arbitrage(
                    buy_exchange="binance_perpetual",
                    sell_exchange="hyperliquid_perpetual",
                    market=market,
                    spread=binance_hyper_spread,
                    params=params
                )

        except Exception as e:
            logger.error(f"Error executing arbitrage for {market}: {e}")

    def execute_arbitrage(self, buy_exchange: str, sell_exchange: str, 
                         market: str, spread: Decimal, params: StrategyParameters):
        """Execute arbitrage trades."""
        try:
            # Calculate position size
            balance = min(
                self.get_available_balance(buy_exchange),
                self.get_available_balance(sell_exchange)
            )
            position_size = min(
                balance * self.max_position_size,
                balance * Decimal(str(params.leverage))
            )

            # Place orders
            buy_order = self.place_order(
                connector_name=buy_exchange,
                trading_pair=market,
                order_type=OrderType.MARKET,
                trade_type=TradeType.BUY,
                amount=position_size,
                price=None  # Market order
            )

            sell_order = self.place_order(
                connector_name=sell_exchange,
                trading_pair=market,
                order_type=OrderType.MARKET,
                trade_type=TradeType.SELL,
                amount=position_size,
                price=None  # Market order
            )

            # Track orders
            self.active_orders[market] = [buy_order, sell_order]
            
            logger.info(f"Executed arbitrage for {market}: "
                       f"Buy on {buy_exchange}, Sell on {sell_exchange}, "
                       f"Size: {position_size}, Spread: {spread}")

        except Exception as e:
            logger.error(f"Error executing arbitrage trades: {e}")

    async def check_and_close_positions(self, market: str):
        """Check and close positions if conditions are met."""
        position = self.positions.get(market)
        if not position:
            return

        try:
            # Calculate current PnL
            entry_price = position['entry_price']
            current_price = self.get_price(position['exchange'], market, 
                                         is_buy=position['is_long'])
            pnl = (current_price - entry_price) / entry_price

            # Close position if target reached or stop loss hit
            if pnl >= Decimal("0.01") or pnl <= Decimal("-0.005"):
                await self.close_position(market, position)

        except Exception as e:
            logger.error(f"Error checking position for {market}: {e}")

    async def close_position(self, market: str, position: Dict):
        """Close an open position."""
        try:
            order = self.place_order(
                connector_name=position['exchange'],
                trading_pair=market,
                order_type=OrderType.MARKET,
                trade_type=TradeType.SELL if position['is_long'] else TradeType.BUY,
                amount=position['size'],
                price=None
            )

            logger.info(f"Closed position for {market}: Size {position['size']}")
            del self.positions[market]

        except Exception as e:
            logger.error(f"Error closing position for {market}: {e}")

    def close_all_positions(self):
        """Close all open positions."""
        for market in list(self.positions.keys()):
            asyncio.create_task(self.close_position(market, self.positions[market]))

    def did_fill_order(self, event: Union[BuyOrderCompleted, SellOrderCompleted]):
        """Called when an order is filled."""
        self.trade_count += 1
        self.total_pnl += event.fee_amount
        logger.info(f"Order filled - {event.order_type} {event.trading_pair}")

    def format_status(self) -> str:
        """Format status for display in Hummingbot."""
        lines = []
        lines.append("Funding Enhanced Arbitrage Strategy")
        lines.append(f"Total PnL: {self.total_pnl:.4f}")
        lines.append(f"Total Trades: {self.trade_count}")
        
        for market, params in self.current_parameters.items():
            lines.append(f"\n{market}:")
            lines.append(f"  Direction: {params.direction}")
            lines.append(f"  Leverage: {params.leverage}")
            lines.append(f"  Entry Threshold: {params.entry_threshold}")
        
        return "\n".join(lines)

    def calculate_funding_impact(self, market: str) -> Decimal:
        """Calculate the impact of funding rates on position profitability"""
        try:
            funding_data = self.funding_client.fetch_latest_funding_rates([market])
            if funding_data.empty:
                return Decimal("0")
                
            current_rate = Decimal(str(funding_data['current_funding_rate'].iloc[0]))
            predicted_rate = Decimal(str(funding_data['predicted_funding_rate'].iloc[0]))
            
            # Calculate 8-hour impact
            funding_impact = (current_rate + predicted_rate) * 3  # 3 funding periods per day
            return funding_impact
            
        except Exception as e:
            logger.error(f"Error calculating funding impact: {e}")
            return Decimal("0")

    def should_open_new_position(self, market: str) -> bool:
        """Determine if we should open a new position based on various factors"""
        try:
            # Check maximum positions
            if len(self.positions) >= self.max_active_positions:
                return False
                
            # Check existing position
            if market in self.positions:
                return False
                
            # Check funding payment timing
            last_payment = self.last_funding_payment.get(market)
            if last_payment and datetime.now() - last_payment < timedelta(hours=1):
                return False
                
            # Check market volatility (implement your own volatility calculation)
            if self.is_market_volatile(market):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking position eligibility: {e}")
            return False

    def is_market_volatile(self, market: str) -> bool:
        """Check if market is too volatile for safe trading"""
        try:
            # Get recent prices
            recent_prices = self.get_recent_prices(market, lookback_periods=12)  # Last hour
            if not recent_prices:
                return True
                
            # Calculate volatility
            volatility = self.calculate_volatility(recent_prices)
            return volatility > Decimal("0.02")  # 2% threshold
            
        except Exception as e:
            logger.error(f"Error checking market volatility: {e}")
            return True

    def get_recent_prices(self, market: str, lookback_periods: int) -> List[Decimal]:
        """Get recent price data for volatility calculation"""
        # Implement based on your data source
        pass

    def calculate_volatility(self, prices: List[Decimal]) -> Decimal:
        """Calculate price volatility"""
        if not prices or len(prices) < 2:
            return Decimal("999")  # High volatility if no data
            
        returns = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
        ]
        
        # Calculate standard deviation of returns
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return Decimal(str(variance ** Decimal("0.5")))

    def record_trade(self, 
                    market: str,
                    side: str,
                    size: Decimal,
                    price: Decimal,
                    pnl: Optional[Decimal] = None):
        """Record trade details for analysis"""
        trade = {
            'timestamp': datetime.now(),
            'market': market,
            'side': side,
            'size': size,
            'price': price,
            'pnl': pnl,
            'funding_rate': self.calculate_funding_impact(market)
        }
        self.trade_history.append(trade)
        
        # Limit history size
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]

def main():
    # Initialize and start the strategy
    strategy = FundingEnhancedArbitrage(
        supabase_url="your_supabase_url",
        supabase_key="your_supabase_key"
    )
    strategy.run()

if __name__ == "__main__":
    main()