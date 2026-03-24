"""
Simian Agent Trading Capability

This module handles autonomous prediction market trading for Simian agents,
focusing on Polymarket and other prediction markets with risk management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import time
import json

import aiohttp
from web3 import Web3


logger = logging.getLogger(__name__)


class MarketSide(Enum):
    """Market sides for prediction markets."""
    YES = "yes"
    NO = "no"
    LONG = "long"
    SHORT = "short"


class OrderType(Enum):
    """Order types for trading."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class MarketStatus(Enum):
    """Market status states."""
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"
    PAUSED = "paused"


@dataclass
class MarketInfo:
    """Information about a prediction market."""
    market_id: str
    title: str
    description: str
    category: str
    end_date: int
    resolution_source: str
    status: MarketStatus = MarketStatus.ACTIVE
    
    # Current market data
    yes_price: Decimal = Decimal('0.5')
    no_price: Decimal = Decimal('0.5')
    volume_24h: Decimal = Decimal('0')
    liquidity: Decimal = Decimal('0')
    
    # Metadata
    created_at: int = 0
    tags: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=lambda: ["Yes", "No"])


@dataclass
class Position:
    """Trading position information."""
    market_id: str
    side: MarketSide
    size: Decimal
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal('0')
    opened_at: int = 0
    last_updated: int = 0


@dataclass
class TradeOrder:
    """Trading order information."""
    order_id: str
    market_id: str
    side: MarketSide
    order_type: OrderType
    size: Decimal
    price: Decimal
    filled_size: Decimal = Decimal('0')
    status: str = "pending"
    created_at: int = 0
    updated_at: int = 0


class TradingStrategy:
    """Base class for trading strategies."""
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': Decimal('0'),
            'max_drawdown': Decimal('0'),
            'sharpe_ratio': 0.0
        }
    
    async def analyze_market(self, market: MarketInfo) -> Dict[str, Union[float, str, bool]]:
        """
        Analyze a market and return trading signals.
        
        Returns:
            Dictionary containing:
            - signal: "buy_yes", "buy_no", "sell", "hold"
            - confidence: 0.0 to 1.0
            - reasoning: Text explanation
            - should_trade: boolean
        """
        raise NotImplementedError("Subclasses must implement analyze_market")
    
    async def calculate_position_size(
        self, 
        signal_confidence: float, 
        current_price: Decimal,
        available_capital: Decimal
    ) -> Decimal:
        """Calculate optimal position size based on risk parameters."""
        # Kelly Criterion with confidence scaling
        kelly_fraction = Decimal(str(signal_confidence * 0.1))  # Max 10% of capital
        max_position = available_capital * kelly_fraction
        
        # Apply additional risk constraints
        min_trade_size = Decimal('10')  # $10 minimum
        max_trade_size = available_capital * Decimal('0.05')  # 5% max per trade
        
        position_size = min(max_position, max_trade_size)
        position_size = max(position_size, min_trade_size)
        
        return position_size


class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy for prediction markets."""
    
    def __init__(self, config: Dict):
        super().__init__("momentum", config)
        self.price_history: Dict[str, List[Tuple[int, Decimal]]] = {}
        self.momentum_threshold = Decimal(str(config.get('momentum_threshold', 0.1)))
        self.volume_threshold = Decimal(str(config.get('volume_threshold', 1000)))
    
    async def analyze_market(self, market: MarketInfo) -> Dict[str, Union[float, str, bool]]:
        """Analyze momentum signals in prediction markets."""
        # Check if we have enough volume to trade
        if market.volume_24h < self.volume_threshold:
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reasoning': 'Insufficient volume for momentum strategy',
                'should_trade': False
            }
        
        # Get price history
        if market.market_id not in self.price_history:
            self.price_history[market.market_id] = []
        
        history = self.price_history[market.market_id]
        current_time = int(time.time())
        history.append((current_time, market.yes_price))
        
        # Keep only last 24 hours
        cutoff_time = current_time - (24 * 3600)
        history = [(t, p) for t, p in history if t > cutoff_time]
        self.price_history[market.market_id] = history
        
        if len(history) < 5:  # Need at least 5 data points
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reasoning': 'Insufficient price history',
                'should_trade': False
            }
        
        # Calculate momentum
        prices = [p for _, p in history]
        short_ma = sum(prices[-3:]) / 3  # 3-period average
        long_ma = sum(prices[-5:]) / 5   # 5-period average
        
        momentum = (short_ma - long_ma) / long_ma
        abs_momentum = abs(momentum)
        
        # Generate signals
        if abs_momentum > self.momentum_threshold:
            if momentum > 0:
                signal = 'buy_yes'
                reasoning = f'Strong upward momentum: {float(momentum):.3f}'
            else:
                signal = 'buy_no'
                reasoning = f'Strong downward momentum: {float(momentum):.3f}'
            
            confidence = min(float(abs_momentum) * 2, 1.0)  # Scale momentum to confidence
            should_trade = True
        else:
            signal = 'hold'
            reasoning = f'Weak momentum: {float(momentum):.3f}'
            confidence = 0.0
            should_trade = False
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'should_trade': should_trade
        }


class PolymarketTrader:
    """Polymarket API trader for Simian agents."""
    
    def __init__(self, api_key: Optional[str] = None, testnet: bool = False):
        self.api_key = api_key
        self.base_url = "https://gamma-api.polymarket.com" if not testnet else "https://gamma-api-staging.polymarket.com"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Trading state
        self.positions: Dict[str, Position] = {}
        self.active_orders: Dict[str, TradeOrder] = {}
        
        # Risk management
        self.max_daily_trades = 10
        self.max_position_size = Decimal('1000')  # $1000
        self.daily_trade_count = 0
        self.last_trade_date = ""
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self.session:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_active_markets(self, category: Optional[str] = None) -> List[MarketInfo]:
        """Fetch active prediction markets."""
        session = await self._get_session()
        url = f"{self.base_url}/markets"
        
        params = {'active': 'true'}
        if category:
            params['category'] = category
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._parse_market_data(market) for market in data]
                else:
                    logger.error(f"Failed to fetch markets: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    async def get_market_details(self, market_id: str) -> Optional[MarketInfo]:
        """Get detailed information about a specific market."""
        session = await self._get_session()
        url = f"{self.base_url}/markets/{market_id}"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_market_data(data)
                else:
                    logger.error(f"Failed to fetch market {market_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching market details: {e}")
            return None
    
    def _parse_market_data(self, data: Dict) -> MarketInfo:
        """Parse market data from API response."""
        return MarketInfo(
            market_id=data.get('id', ''),
            title=data.get('question', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            end_date=data.get('end_date_iso', 0),
            resolution_source=data.get('resolution_source', ''),
            yes_price=Decimal(str(data.get('yes_price', 0.5))),
            no_price=Decimal(str(data.get('no_price', 0.5))),
            volume_24h=Decimal(str(data.get('volume_24hr', 0))),
            liquidity=Decimal(str(data.get('liquidity', 0))),
            tags=data.get('tags', [])
        )
    
    async def place_order(
        self,
        market_id: str,
        side: MarketSide,
        size: Decimal,
        price: Decimal,
        order_type: OrderType = OrderType.LIMIT
    ) -> Optional[str]:
        """
        Place a trading order.
        
        Returns:
            Order ID if successful, None if failed
        """
        # Risk checks
        if not self._can_place_order(size):
            logger.warning("Order rejected by risk management")
            return None
        
        session = await self._get_session()
        url = f"{self.base_url}/orders"
        
        order_data = {
            'market_id': market_id,
            'side': side.value,
            'size': str(size),
            'price': str(price),
            'type': order_type.value
        }
        
        try:
            async with session.post(url, json=order_data) as response:
                if response.status == 201:
                    data = await response.json()
                    order_id = data.get('id')
                    
                    # Track the order
                    self.active_orders[order_id] = TradeOrder(
                        order_id=order_id,
                        market_id=market_id,
                        side=side,
                        order_type=order_type,
                        size=size,
                        price=price,
                        created_at=int(time.time())
                    )
                    
                    self._increment_daily_trades()
                    logger.info(f"Order placed: {order_id}")
                    return order_id
                else:
                    logger.error(f"Failed to place order: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    def _can_place_order(self, size: Decimal) -> bool:
        """Check if order passes risk management rules."""
        # Check daily trade limit
        current_date = time.strftime('%Y-%m-%d')
        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
        
        if self.daily_trade_count >= self.max_daily_trades:
            logger.warning("Daily trade limit exceeded")
            return False
        
        # Check position size
        if size > self.max_position_size:
            logger.warning(f"Order size {size} exceeds max position size {self.max_position_size}")
            return False
        
        return True
    
    def _increment_daily_trades(self):
        """Increment daily trade counter."""
        current_date = time.strftime('%Y-%m-%d')
        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
        
        self.daily_trade_count += 1
    
    async def update_positions(self):
        """Update current positions from the exchange."""
        session = await self._get_session()
        url = f"{self.base_url}/positions"
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for position_data in data:
                        position = self._parse_position_data(position_data)
                        self.positions[position.market_id] = position
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    def _parse_position_data(self, data: Dict) -> Position:
        """Parse position data from API response."""
        return Position(
            market_id=data.get('market_id', ''),
            side=MarketSide(data.get('side', 'yes')),
            size=Decimal(str(data.get('size', 0))),
            entry_price=Decimal(str(data.get('entry_price', 0))),
            current_price=Decimal(str(data.get('current_price', 0))),
            unrealized_pnl=Decimal(str(data.get('unrealized_pnl', 0))),
            realized_pnl=Decimal(str(data.get('realized_pnl', 0))),
            last_updated=int(time.time())
        )
    
    def get_portfolio_summary(self) -> Dict[str, Union[Decimal, int]]:
        """Get portfolio performance summary."""
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        return {
            'total_positions': len(self.positions),
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_pnl': total_pnl,
            'active_orders': len(self.active_orders)
        }


class SimianTradingAgent:
    """Main trading agent that combines strategies and execution."""
    
    def __init__(
        self,
        agent_id: str,
        trader: PolymarketTrader,
        strategies: List[TradingStrategy],
        risk_params: Dict
    ):
        self.agent_id = agent_id
        self.trader = trader
        self.strategies = strategies
        self.risk_params = risk_params
        
        self.is_active = False
        self.last_run = 0
        
    async def start_trading(self):
        """Start the trading loop."""
        self.is_active = True
        logger.info(f"Trading agent {self.agent_id} started")
        
        while self.is_active:
            try:
                await self._trading_cycle()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Trading cycle error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop_trading(self):
        """Stop the trading loop."""
        self.is_active = False
        logger.info(f"Trading agent {self.agent_id} stopped")
    
    async def _trading_cycle(self):
        """Execute one trading cycle."""
        # Get active markets
        markets = await self.trader.get_active_markets()
        
        # Update positions
        await self.trader.update_positions()
        
        # Analyze each market with all strategies
        for market in markets:
            await self._analyze_and_trade(market)
    
    async def _analyze_and_trade(self, market: MarketInfo):
        """Analyze a market and potentially place trades."""
        signals = []
        
        # Get signals from all strategies
        for strategy in self.strategies:
            try:
                signal = await strategy.analyze_market(market)
                signals.append((strategy, signal))
            except Exception as e:
                logger.error(f"Strategy {strategy.name} failed for market {market.market_id}: {e}")
        
        # Combine signals (simple majority voting for now)
        buy_yes_votes = sum(1 for _, signal in signals if signal['signal'] == 'buy_yes' and signal['should_trade'])
        buy_no_votes = sum(1 for _, signal in signals if signal['signal'] == 'buy_no' and signal['should_trade'])
        
        if buy_yes_votes > buy_no_votes and buy_yes_votes >= len(self.strategies) / 2:
            # Execute buy YES
            confidence = sum(signal['confidence'] for _, signal in signals if signal['signal'] == 'buy_yes') / buy_yes_votes
            await self._execute_trade(market, MarketSide.YES, confidence)
        
        elif buy_no_votes > buy_yes_votes and buy_no_votes >= len(self.strategies) / 2:
            # Execute buy NO
            confidence = sum(signal['confidence'] for _, signal in signals if signal['signal'] == 'buy_no') / buy_no_votes
            await self._execute_trade(market, MarketSide.NO, confidence)
    
    async def _execute_trade(self, market: MarketInfo, side: MarketSide, confidence: float):
        """Execute a trade based on analysis."""
        # Calculate position size
        available_capital = Decimal('1000')  # TODO: Get from wallet/config
        
        strategy = self.strategies[0]  # Use first strategy for position sizing
        price = market.yes_price if side == MarketSide.YES else market.no_price
        position_size = await strategy.calculate_position_size(confidence, price, available_capital)
        
        # Place the order
        order_id = await self.trader.place_order(
            market_id=market.market_id,
            side=side,
            size=position_size,
            price=price
        )
        
        if order_id:
            logger.info(f"Trade executed: {side.value} {position_size} @ {price} for market {market.market_id}")


# TODO: Implement the following features:
# - [ ] Integration with existing polymarket-arb codebase
# - [ ] Advanced strategy implementations (mean reversion, arbitrage, etc.)
# - [ ] Real-time market data feeds and WebSocket connections
# - [ ] Portfolio risk management and position sizing optimization
# - [ ] Trade execution optimization (slippage minimization, timing)
# - [ ] Performance analytics and strategy backtesting
# - [ ] Integration with Simian delegation verification
# - [ ] Multi-exchange support (Kalshi, Manifold, etc.)
# - [ ] Automated market making capabilities
# - [ ] News/sentiment analysis for trading signals
# - [ ] Stop-loss and take-profit order management
# - [ ] Tax-loss harvesting and accounting integration