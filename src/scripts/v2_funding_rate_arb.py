import os
from decimal import Decimal
from typing import Dict, List, Set
import pandas as pd
from datetime import datetime, timedelta
import logging
from pydantic import Field, validator
from supabase import create_client

from hummingbot.client.config.config_data_types import ClientFieldData
from hummingbot.client.ui.interface_utils import format_df_for_printout
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.clock import Clock
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, PriceType, TradeType
from hummingbot.core.event.events import FundingPaymentCompletedEvent
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase
from hummingbot.strategy_v2.executors.position_executor.data_types import PositionExecutorConfig, TripleBarrierConfig
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, StopExecutorAction

logger = logging.getLogger(__name__)

class FundingRateArbitrageConfig(StrategyV2ConfigBase):
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

    leverage: int = Field(
        default=20,
        gt=0,
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter leverage (1-100): ",
            prompt_on_new=True
        )
    )

    min_funding_rate_profitability: Decimal = Field(
        default=Decimal("0.001"),
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter min funding rate profitability: ",
            prompt_on_new=True
        )
    )

    position_size_quote: Decimal = Field(
        default=Decimal("100"),
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter position size in quote currency: ",
            prompt_on_new=True
        )
    )

    profitability_to_take_profit: Decimal = Field(
        default=Decimal("0.01"),
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter take profit threshold: ",
            prompt_on_new=True
        )
    )

    funding_rate_diff_stop_loss: Decimal = Field(
        default=Decimal("-0.001"),
        client_data=ClientFieldData(
            prompt=lambda mi: "Enter funding rate difference stop loss: ",
            prompt_on_new=True
        )
    )

class FundingRateArbitrage(StrategyV2Base):
    quote_markets_map = {
        "hyperliquid_perpetual_testnet": "USD",
        "binance_perpetual_testnet": "USDT"
    }
    
    funding_payment_interval_map = {
        "binance_perpetual_testnet": 60 * 60 * 8,
        "hyperliquid_perpetual_testnet": 60 * 60 * 1
    }
    
    funding_profitability_interval = 60 * 60 * 24

    def __init__(self, connectors: Dict[str, ConnectorBase], config: FundingRateArbitrageConfig):
        super().__init__(connectors, config)
        self.config = config
        
        # Initialize Supabase client
        self.supabase = create_client(config.supabase_url, config.supabase_key)
        
        # Initialize markets based on available pairs in Supabase
        self.initialize_markets()
        
        self.active_funding_arbitrages = {}
        self.opportunity_tracker = {}
        self.last_funding_update = datetime.now()

    def initialize_markets(self):
        """Initialize markets based on available pairs in Supabase"""
        try:
            # Fetch available pairs from Supabase
            response = self.supabase.table('funding_rates').select('symbol').execute()
            available_pairs = pd.DataFrame(response.data)
            
            if available_pairs.empty:
                logger.warning("No pairs found in Supabase")
                return
            
            # Filter and format pairs for each connector
            self.markets = {
                "hyperliquid_perpetual_testnet": [],
                "binance_perpetual_testnet": []
            }
            
            for pair in available_pairs['symbol'].unique():
                token = pair.split('-')[0]
                self.markets["hyperliquid_perpetual_testnet"].append(f"{token}-USD")
                self.markets["binance_perpetual_testnet"].append(f"{token}-USDT")
                
            logger.info(f"Initialized markets: {self.markets}")
            
        except Exception as e:
            logger.error(f"Error initializing markets: {e}")

    async def get_funding_opportunities(self) -> pd.DataFrame:
        """Fetch and analyze funding rate opportunities"""
        try:
            # Fetch latest funding rates
            response = self.supabase.table('funding_rates').select(
                'symbol',
                'exchange',
                'current_funding_rate',
                'predicted_funding_rate',
                'timestamp',
                'open_interest',
                'volume_24h'
            ).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            
            # Calculate opportunity metrics
            opportunities = []
            for token in df['symbol'].unique():
                token_data = df[df['symbol'] == token]
                
                for c1 in self.markets.keys():
                    for c2 in self.markets.keys():
                        if c1 >= c2:
                            continue
                            
                        c1_data = token_data[token_data['exchange'] == c1].iloc[0] if not token_data[token_data['exchange'] == c1].empty else None
                        c2_data = token_data[token_data['exchange'] == c2].iloc[0] if not token_data[token_data['exchange'] == c2].empty else None
                        
                        if c1_data is not None and c2_data is not None:
                            # Calculate metrics
                            funding_diff = c1_data['current_funding_rate'] - c2_data['current_funding_rate']
                            predicted_diff = c1_data['predicted_funding_rate'] - c2_data['predicted_funding_rate']
                            avg_volume = (c1_data['volume_24h'] + c2_data['volume_24h']) / 2
                            min_oi = min(c1_data['open_interest'], c2_data['open_interest'])
                            
                            opportunities.append({
                                'token': token,
                                'connector_1': c1,
                                'connector_2': c2,
                                'funding_diff': funding_diff,
                                'predicted_diff': predicted_diff,
                                'avg_volume': avg_volume,
                                'min_oi': min_oi,
                                'opportunity_score': self.calculate_opportunity_score(
                                    funding_diff, predicted_diff, avg_volume, min_oi
                                )
                            })
            
            return pd.DataFrame(opportunities).sort_values('opportunity_score', ascending=False)
            
        except Exception as e:
            logger.error(f"Error fetching funding opportunities: {e}")
            return pd.DataFrame()

    def calculate_opportunity_score(self, 
                                 funding_diff: float,
                                 predicted_diff: float,
                                 avg_volume: float,
                                 min_oi: float) -> float:
        """Calculate a score for the opportunity based on multiple factors"""
        try:
            # Normalize metrics
            funding_score = abs(funding_diff) * 100  # Convert to percentage
            prediction_score = abs(predicted_diff) * 100
            volume_score = min(avg_volume / 1_000_000, 1)  # Cap at 1M volume
            oi_score = min(min_oi / 1_000_000, 1)  # Cap at 1M OI
            
            # Weight the factors
            weights = {
                'funding': 0.4,
                'prediction': 0.3,
                'volume': 0.15,
                'oi': 0.15
            }
            
            # Calculate final score
            score = (
                funding_score * weights['funding'] +
                prediction_score * weights['prediction'] +
                volume_score * weights['volume'] +
                oi_score * weights['oi']
            )
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0

    def format_status(self) -> str:
        """Enhanced status display with opportunity analysis"""
        lines = []
        lines.append("\n=== Funding Rate Arbitrage Opportunities ===\n")
        
        try:
            opportunities = self.get_funding_opportunities()
            if not opportunities.empty:
                # Format top opportunities
                top_opps = opportunities.head(5)
                lines.append("Top 5 Opportunities:")
                lines.append(format_df_for_printout(
                    top_opps[['token', 'connector_1', 'connector_2', 'funding_diff', 'opportunity_score']],
                    table_format="psql"
                ))
                
                # Add active positions
                if self.active_funding_arbitrages:
                    lines.append("\nActive Positions:")
                    for token, info in self.active_funding_arbitrages.items():
                        lines.append(f"Token: {token}")
                        lines.append(f"Direction: Long {info['connector_1']}, Short {info['connector_2']}")
                        lines.append(f"PnL: {info['pnl']:.4f}")
                        lines.append("---")
            else:
                lines.append("No opportunities found")
                
        except Exception as e:
            lines.append(f"Error formatting status: {e}")
            
        return "\n".join(lines)

    def start(self, clock: Clock, timestamp: float) -> None:
        """
        Start the strategy.
        :param clock: Clock to use.
        :param timestamp: Current time.
        """
        self._last_timestamp = timestamp
        self.apply_initial_setting()

    def apply_initial_setting(self):
        for connector_name, connector in self.connectors.items():
            if self.is_perpetual(connector_name):
                position_mode = PositionMode.ONEWAY if connector_name == "hyperliquid_perpetual_testnet" else PositionMode.HEDGE
                connector.set_position_mode(position_mode)
                for trading_pair in self.market_data_provider.get_trading_pairs(connector_name):
                    connector.set_leverage(trading_pair, self.config.leverage)

    def get_funding_info_by_token(self, token):
        """
        This method provides the funding rates across all the connectors
        """
        funding_rates = {}
        for connector_name, connector in self.connectors.items():
            trading_pair = self.get_trading_pair_for_connector(token, connector_name)
            funding_rates[connector_name] = connector.get_funding_info(trading_pair)
        return funding_rates

    def get_current_profitability_after_fees(self, token: str, connector_1: str, connector_2: str, side: TradeType):
        """
        This methods compares the profitability of buying at market in the two exchanges. If the side is TradeType.BUY
        means that the operation is long on connector 1 and short on connector 2.
        """
        trading_pair_1 = self.get_trading_pair_for_connector(token, connector_1)
        trading_pair_2 = self.get_trading_pair_for_connector(token, connector_2)

        connector_1_price = Decimal(self.market_data_provider.get_price_for_quote_volume(
            connector_name=connector_1,
            trading_pair=trading_pair_1,
            quote_volume=self.config.position_size_quote,
            is_buy=side == TradeType.BUY,
        ).result_price)
        connector_2_price = Decimal(self.market_data_provider.get_price_for_quote_volume(
            connector_name=connector_2,
            trading_pair=trading_pair_2,
            quote_volume=self.config.position_size_quote,
            is_buy=side != TradeType.BUY,
        ).result_price)
        estimated_fees_connector_1 = self.connectors[connector_1].get_fee(
            base_currency=trading_pair_1.split("-")[0],
            quote_currency=trading_pair_1.split("-")[1],
            order_type=OrderType.MARKET,
            order_side=TradeType.BUY,
            amount=self.config.position_size_quote / connector_1_price,
            price=connector_1_price,
            is_maker=False,
            position_action=PositionAction.OPEN
        ).percent
        estimated_fees_connector_2 = self.connectors[connector_2].get_fee(
            base_currency=trading_pair_2.split("-")[0],
            quote_currency=trading_pair_2.split("-")[1],
            order_type=OrderType.MARKET,
            order_side=TradeType.BUY,
            amount=self.config.position_size_quote / connector_2_price,
            price=connector_2_price,
            is_maker=False,
            position_action=PositionAction.OPEN
        ).percent

        if side == TradeType.BUY:
            estimated_trade_pnl_pct = (connector_2_price - connector_1_price) / connector_1_price
        else:
            estimated_trade_pnl_pct = (connector_1_price - connector_2_price) / connector_2_price
        return estimated_trade_pnl_pct - estimated_fees_connector_1 - estimated_fees_connector_2

    def get_most_profitable_combination(self, funding_info_report: Dict):
        best_combination = None
        highest_profitability = 0
        for connector_1 in funding_info_report:
            for connector_2 in funding_info_report:
                if connector_1 != connector_2:
                    rate_connector_1 = self.get_normalized_funding_rate_in_seconds(funding_info_report, connector_1)
                    rate_connector_2 = self.get_normalized_funding_rate_in_seconds(funding_info_report, connector_2)
                    funding_rate_diff = abs(rate_connector_1 - rate_connector_2) * self.funding_profitability_interval
                    if funding_rate_diff > highest_profitability:
                        trade_side = TradeType.BUY if rate_connector_1 < rate_connector_2 else TradeType.SELL
                        highest_profitability = funding_rate_diff
                        best_combination = (connector_1, connector_2, trade_side, funding_rate_diff)
        return best_combination

    def get_normalized_funding_rate_in_seconds(self, funding_info_report, connector_name):
        return funding_info_report[connector_name].rate / self.funding_payment_interval_map.get(connector_name, 60 * 60 * 8)

    def create_actions_proposal(self) -> List[CreateExecutorAction]:
        """
        In this method we are going to evaluate if a new set of positions has to be created for each of the tokens that
        don't have an active arbitrage.
        More filters can be applied to limit the creation of the positions, since the current logic is only checking for
        positive pnl between funding rate. Is logged and computed the trading profitability at the time for entering
        at market to open the possibilities for other people to create variations like sending limit position executors
        and if one gets filled buy market the other one to improve the entry prices.
        """
        create_actions = []
        for token in self.config.tokens:
            if token not in self.active_funding_arbitrages:
                funding_info_report = self.get_funding_info_by_token(token)
                best_combination = self.get_most_profitable_combination(funding_info_report)
                connector_1, connector_2, trade_side, expected_profitability = best_combination
                if expected_profitability >= self.config.min_funding_rate_profitability:
                    current_profitability = self.get_current_profitability_after_fees(
                        token, connector_1, connector_2, trade_side
                    )
                    if self.config.trade_profitability_condition_to_enter:
                        if current_profitability < 0:
                            self.logger().info(f"Best Combination: {connector_1} | {connector_2} | {trade_side}"
                                               f"Funding rate profitability: {expected_profitability}"
                                               f"Trading profitability after fees: {current_profitability}"
                                               f"Trade profitability is negative, skipping...")
                            continue
                    self.logger().info(f"Best Combination: {connector_1} | {connector_2} | {trade_side}"
                                       f"Funding rate profitability: {expected_profitability}"
                                       f"Trading profitability after fees: {current_profitability}"
                                       f"Starting executors...")
                    position_executor_config_1, position_executor_config_2 = self.get_position_executors_config(token, connector_1, connector_2, trade_side)
                    self.active_funding_arbitrages[token] = {
                        "connector_1": connector_1,
                        "connector_2": connector_2,
                        "executors_ids": [position_executor_config_1.id, position_executor_config_2.id],
                        "side": trade_side,
                        "funding_payments": [],
                    }
                    return [CreateExecutorAction(executor_config=position_executor_config_1),
                            CreateExecutorAction(executor_config=position_executor_config_2)]
        return create_actions

    def stop_actions_proposal(self) -> List[StopExecutorAction]:
        """
        Once the funding rate arbitrage is created we are going to control the funding payments pnl and the current
        pnl of each of the executors at the cost of closing the open position at market.
        If that PNL is greater than the profitability_to_take_profit
        """
        stop_executor_actions = []
        for token, funding_arbitrage_info in self.active_funding_arbitrages.items():
            executors = self.filter_executors(
                executors=self.get_all_executors(),
                filter_func=lambda x: x.id in funding_arbitrage_info["executors_ids"]
            )
            funding_payments_pnl = sum(funding_payment.amount for funding_payment in funding_arbitrage_info["funding_payments"])
            executors_pnl = sum(executor.net_pnl_quote for executor in executors)
            take_profit_condition = executors_pnl + funding_payments_pnl > self.config.profitability_to_take_profit * self.config.position_size_quote
            funding_info_report = self.get_funding_info_by_token(token)
            if funding_arbitrage_info["side"] == TradeType.BUY:
                funding_rate_diff = self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_2"]) - self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_1"])
            else:
                funding_rate_diff = self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_1"]) - self.get_normalized_funding_rate_in_seconds(funding_info_report, funding_arbitrage_info["connector_2"])
            current_funding_condition = funding_rate_diff * self.funding_profitability_interval < self.config.funding_rate_diff_stop_loss
            if take_profit_condition:
                self.logger().info("Take profit profitability reached, stopping executors")
                self.stopped_funding_arbitrages[token].append(funding_arbitrage_info)
                stop_executor_actions.extend([StopExecutorAction(executor_id=executor.id) for executor in executors])
            elif current_funding_condition:
                self.logger().info("Funding rate difference reached for stop loss, stopping executors")
                self.stopped_funding_arbitrages[token].append(funding_arbitrage_info)
                stop_executor_actions.extend([StopExecutorAction(executor_id=executor.id) for executor in executors])
        return stop_executor_actions

    def did_complete_funding_payment(self, funding_payment_completed_event: FundingPaymentCompletedEvent):
        """
        Based on the funding payment event received, check if one of the active arbitrages matches to add the event
        to the list.
        """
        token = funding_payment_completed_event.trading_pair.split("-")[0]
        if token in self.active_funding_arbitrages:
            self.active_funding_arbitrages[token]["funding_payments"].append(funding_payment_completed_event)

    def get_position_executors_config(self, token, connector_1, connector_2, trade_side):
        price = self.market_data_provider.get_price_by_type(
            connector_name=connector_1,
            trading_pair=self.get_trading_pair_for_connector(token, connector_1),
            price_type=PriceType.MidPrice
        )
        position_amount = self.config.position_size_quote / price

        position_executor_config_1 = PositionExecutorConfig(
            timestamp=self.current_timestamp,
            connector_name=connector_1,
            trading_pair=self.get_trading_pair_for_connector(token, connector_1),
            side=trade_side,
            amount=position_amount,
            leverage=self.config.leverage,
            triple_barrier_config=TripleBarrierConfig(open_order_type=OrderType.MARKET),
        )
        position_executor_config_2 = PositionExecutorConfig(
            timestamp=self.current_timestamp,
            connector_name=connector_2,
            trading_pair=self.get_trading_pair_for_connector(token, connector_2),
            side=TradeType.BUY if trade_side == TradeType.SELL else TradeType.SELL,
            amount=position_amount,
            leverage=self.config.leverage,
            triple_barrier_config=TripleBarrierConfig(open_order_type=OrderType.MARKET),
        )
        return position_executor_config_1, position_executor_config_2
