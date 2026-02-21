"""
Core trading engine orchestrator.
Manages WebSocket data feed, signal generation, order execution, and persistence.
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from .models import (
    PriceTick, TradingSignal, Order, OrderStatus, SignalType,
    EngineConfig, PerformanceMetrics, MovingAverageState
)
from .websocket import BinanceWebSocketConnector
from .signals import SignalGenerator
from .database import SQLiteBackend

logger = logging.getLogger(__name__)


class TradingEngine:
    """
    Real-time event-driven trading engine.
    
    Listens to market data via WebSocket, calculates signals, executes orders,
    and persists all activity to database.
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize trading engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config
        self.start_time = datetime.utcnow()
        
        # Components
        self.websocket: Optional[BinanceWebSocketConnector] = None
        self.signal_gen = SignalGenerator(
            sma_short_period=config.sma_short_period,
            sma_long_period=config.sma_long_period
        )
        self.database = SQLiteBackend(db_path="trading_signals.db")
        
        # Metrics
        self.metrics = PerformanceMetrics()
        self.last_prices: dict[str, Decimal] = {}
        
        # Position tracking (for risk management)
        self.open_positions: dict[str, list[Order]] = {}
        
        logger.info(f"TradingEngine initialized with config: {config}")
    
    async def initialize(self) -> None:
        """Initialize all engine components."""
        logger.info("Initializing engine components...")
        
        # Setup database
        await self.database.initialize()
        
        # Setup WebSocket
        self.websocket = BinanceWebSocketConnector(
            symbols=self.config.symbols
        )
        self.websocket.subscribe_to_ticks(self._on_price_tick)
        
        logger.info("Engine initialization complete")
    
    async def _on_price_tick(self, tick: PriceTick) -> None:
        """
        Handle incoming price tick from WebSocket.
        Main event loop for the engine.
        """
        try:
            # Track last price
            self.last_prices[tick.symbol] = tick.price
            
            # Generate signal
            signal = self.signal_gen.generate_signal(tick)
            
            if signal:
                # Save signal
                signal_id = await self.database.save_signal(signal)
                
                # Log signal
                logger.info(
                    f"📊 SIGNAL: {signal.symbol} {signal.signal_type.value} @ ${signal.price} "
                    f"(confidence: {signal.confidence:.1%}) - {signal.reason}"
                )
                
                # Update metrics
                self._update_signal_metrics(signal)
                
                # Generate order if configured
                if self.config.risk_management_enabled:
                    order = self._generate_order_from_signal(signal, signal_id)
                    await self._execute_order(order)
        
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)
    
    def _update_signal_metrics(self, signal: TradingSignal) -> None:
        """Update performance metrics on signal generation."""
        self.metrics.total_signals += 1
        
        if signal.signal_type == SignalType.BUY:
            self.metrics.buy_signals += 1
        elif signal.signal_type == SignalType.SELL:
            self.metrics.sell_signals += 1
        
        self.metrics.last_signal_time = signal.timestamp
    
    def _generate_order_from_signal(self, signal: TradingSignal, signal_id: str) -> Order:
        """
        Generate executable order from trading signal.
        Includes risk management (stop loss, take profit).
        """
        quantity = Decimal(str(self.config.position_size_percent)) / Decimal(100)
        
        stop_loss = None
        take_profit = None
        
        if signal.signal_type == SignalType.BUY:
            # Buy order with risk management
            stop_loss = signal.price * (
                Decimal(1) - Decimal(str(self.config.stop_loss_percent / 100))
            )
            take_profit = signal.price * (
                Decimal(1) + Decimal(str(self.config.take_profit_percent / 100))
            )
        
        elif signal.signal_type == SignalType.SELL:
            # Sell order
            take_profit = signal.price * (
                Decimal(1) - Decimal(str(self.config.take_profit_percent / 100))
            )
            stop_loss = signal.price * (
                Decimal(1) + Decimal(str(self.config.stop_loss_percent / 100))
            )
        
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=signal.symbol,
            signal_id=signal_id,
            signal_type=signal.signal_type,
            quantity=quantity,
            entry_price=signal.price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            notes=signal.reason
        )
        
        return order
    
    async def _execute_order(self, order: Order) -> None:
        """
        Execute order (in simulation, immediately mark as executed).
        In production, would connect to broker API.
        """
        try:
            # Save order to database
            await self.database.save_order(order)
            self.metrics.total_orders += 1
            
            # Simulate instant execution at signal price
            order.status = OrderStatus.EXECUTED
            order.executed_at = datetime.utcnow()
            order.execution_price = order.entry_price
            
            await self.database.update_order(order)
            self.metrics.executed_orders += 1
            
            # Track position
            if order.symbol not in self.open_positions:
                self.open_positions[order.symbol] = []
            self.open_positions[order.symbol].append(order)
            
            logger.info(
                f"📈 ORDER EXECUTED: {order.order_id[:8]}... "
                f"{order.symbol} {order.signal_type.value} "
                f"qty={order.quantity} @ ${order.execution_price}"
            )
        
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            order.status = OrderStatus.FAILED
            self.metrics.failed_orders += 1
            await self.database.update_order(order)
    
    async def run(self) -> None:
        """
        Main engine run loop.
        Connects to data feed and processes events indefinitely.
        """
        try:
            logger.info("🚀 Starting trading engine...")
            
            if self.websocket is None:
                await self.initialize()
            
            # Connect to WebSocket and run
            await self.websocket.connect()
        
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Engine error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the engine."""
        logger.info("🛑 Shutting down trading engine...")
        
        try:
            if self.websocket:
                await self.websocket.disconnect()
            
            await self.database.close()
            
            # Save final metrics
            await self._save_metrics_snapshot()
            
            logger.info("✅ Engine shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _save_metrics_snapshot(self) -> None:
        """Save current performance metrics to database."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Calculate win rate
        if self.metrics.executed_orders > 0:
            # In real system, would check profitable orders
            self.metrics.win_rate = 0.5  # Placeholder
        
        self.metrics.uptime_seconds = int(uptime)
        
        metrics_dict = {
            'total_signals': self.metrics.total_signals,
            'buy_signals': self.metrics.buy_signals,
            'sell_signals': self.metrics.sell_signals,
            'total_orders': self.metrics.total_orders,
            'executed_orders': self.metrics.executed_orders,
            'failed_orders': self.metrics.failed_orders,
            'total_pnl': float(self.metrics.total_pnl),
            'win_rate': self.metrics.win_rate,
            'uptime_seconds': self.metrics.uptime_seconds
        }
        
        await self.database.save_metrics(metrics_dict)
        
        logger.info(
            f"📊 Final Metrics - Signals: {self.metrics.total_signals} "
            f"({self.metrics.buy_signals}B/{self.metrics.sell_signals}S), "
            f"Orders: {self.metrics.executed_orders}/{self.metrics.total_orders} executed, "
            f"Uptime: {uptime:.0f}s"
        )
    
    def get_state_snapshot(self) -> dict:
        """Get current engine state for monitoring."""
        return {
            'timestamp': datetime.utcnow(),
            'is_connected': self.websocket.is_connected if self.websocket else False,
            'last_prices': {k: float(v) for k, v in self.last_prices.items()},
            'sma_states': {
                symbol: {
                    'sma_short': float(v.sma_short) if v.sma_short else None,
                    'sma_long': float(v.sma_long) if v.sma_long else None,
                }
                for symbol, v in self.signal_gen.sma_states.items()
            },
            'metrics': self.metrics.dict(),
            'open_positions': len(self.open_positions),
        }
