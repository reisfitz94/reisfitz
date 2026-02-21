"""
Integration example and test for the Trading Engine.
Demonstrates all major components working together.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from trading_engine import (
    TradingEngine,
    EngineConfig,
    PriceTick,
    SignalGenerator
)

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(message)s'
)

logger = logging.getLogger(__name__)


class SimulatedDataFeed:
    """
    Simulates WebSocket price data for testing without live connection.
    Useful for strategy backtesting and development.
    """
    
    def __init__(self, symbol: str = "BTCUSDT"):
        """Initialize simulated feed with trending price data."""
        self.symbol = symbol
        self.current_price = Decimal("45000")
        self.tick_count = 0
        
        # Simulate uptrend then downtrend
        self.prices = [
            45000, 45100, 45200, 45300, 45400, 45500, 45600, 45700, 45800, 45900,
            46000, 46100, 46200, 46300, 46400, 46500, 46600, 46700, 46800, 46900,
            47000, 47100, 47200, 47300, 47400, 47500, 47400, 47300, 47200, 47100,
            47000, 46900, 46800, 46700, 46600, 46500, 46400, 46300, 46200, 46100,
        ]
    
    async def tick_generator(self):
        """Generate simulated price ticks."""
        for price in self.prices:
            self.tick_count += 1
            tick = PriceTick(
                symbol=self.symbol,
                price=Decimal(str(price)),
                timestamp=datetime.utcnow(),
                volume=Decimal("100")
            )
            
            yield tick
            
            # Simulate Binance ~1-second tick frequency
            await asyncio.sleep(0.1)


async def example_signal_generation():
    """
    Example 1: Signal generation with simulated data.
    Shows how signals are generated from price ticks.
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Signal Generation Demo")
    logger.info("=" * 60)
    
    # Create signal generator with SMA(10, 20)
    signal_gen = SignalGenerator(sma_short_period=10, sma_long_period=20)
    signals_generated = []
    
    # Simulate price feed
    feed = SimulatedDataFeed("BTCUSDT")
    
    async for tick in feed.tick_generator():
        # Generate signal
        signal = signal_gen.generate_signal(tick)
        
        # Get current SMA state
        state = signal_gen.get_state("BTCUSDT")
        
        # Display every 5th tick
        if feed.tick_count % 5 == 0:
            print(f"\nTick #{feed.tick_count}: ${tick.price}")
            print(f"  SMA10: ${state.sma_short}")
            print(f"  SMA20: ${state.sma_long}")
        
        if signal:
            signals_generated.append(signal)
            logger.info(
                f"📊 SIGNAL: {signal.symbol} {signal.signal_type.value} @ ${signal.price} "
                f"| {signal.reason}"
            )
    
    logger.info(f"\nTotal signals generated: {len(signals_generated)}")
    for sig in signals_generated:
        print(f"  - {sig.timestamp.strftime('%H:%M:%S')}: {sig.signal_type.value} @ ${sig.price}")


async def example_engine_initialization():
    """
    Example 2: Full engine initialization and configuration.
    Shows how to set up the complete trading engine.
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Engine Configuration")
    logger.info("=" * 60)
    
    # Create configuration
    config = EngineConfig(
        symbols=["BTCUSDT", "ETHUSDT"],
        sma_short_period=10,
        sma_long_period=20,
        db_url="sqlite:///trading_demo.db",
        websocket_url="wss://stream.binance.com:9443/ws",
        data_feed="binance",
        risk_management_enabled=True,
        position_size_percent=1.0,
        stop_loss_percent=2.0,
        take_profit_percent=5.0
    )
    
    logger.info(f"Configuration created:")
    logger.info(f"  Symbols: {config.symbols}")
    logger.info(f"  SMA Periods: {config.sma_short_period}/{config.sma_long_period}")
    logger.info(f"  Position Size: {config.position_size_percent}%")
    logger.info(f"  Stop Loss: {config.stop_loss_percent}%")
    logger.info(f"  Take Profit: {config.take_profit_percent}%")
    
    # Create engine (don't run, just initialize)
    engine = TradingEngine(config)
    await engine.initialize()
    
    logger.info("Engine initialized successfully")
    logger.info(f"  Signal Generator: SMA({config.sma_short_period}, {config.sma_long_period})")
    logger.info(f"  Database: {engine.database.db_path}")
    
    await engine.database.close()


async def example_pydantic_validation():
    """
    Example 3: Data validation with Pydantic.
    Shows type safety and validation features.
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: Type-Safe Data Validation")
    logger.info("=" * 60)
    
    # Valid data
    tick = PriceTick(
        symbol="BTCUSDT",
        price=Decimal("45000.50"),
        volume=Decimal("1000")
    )
    logger.info(f"✓ Valid tick created: {tick.symbol} @ ${tick.price}")
    
    # Demonstrate validation errors
    validation_tests = [
        ("Negative price", lambda: PriceTick(symbol="BTC", price=Decimal("-100"))),
        ("Invalid symbol format", lambda: PriceTick(symbol="", price=Decimal("100"))),
    ]
    
    for test_name, test_func in validation_tests:
        try:
            test_func()
            logger.info(f"✗ {test_name}: Should have failed!")
        except Exception as e:
            logger.info(f"✓ {test_name}: Caught validation error")
            logger.info(f"  Error: {str(e)[:80]}...")


async def example_metrics_tracking():
    """
    Example 4: Performance metrics tracking.
    Shows how the engine tracks trading performance.
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: Performance Metrics")
    logger.info("=" * 60)
    
    from trading_engine.models import PerformanceMetrics, SignalType
    
    metrics = PerformanceMetrics()
    
    # Simulate trading activity
    metrics.total_signals = 15
    metrics.buy_signals = 8
    metrics.sell_signals = 7
    metrics.total_orders = 14
    metrics.executed_orders = 12
    metrics.failed_orders = 2
    metrics.total_pnl = Decimal("1250.75")
    metrics.win_rate = 0.714
    metrics.uptime_seconds = 3600
    
    logger.info("Current Metrics:")
    logger.info(f"  Signals: {metrics.total_signals} ({metrics.buy_signals}B/{metrics.sell_signals}S)")
    logger.info(f"  Orders: {metrics.executed_orders}/{metrics.total_orders} executed")
    logger.info(f"  Failed: {metrics.failed_orders}")
    logger.info(f"  P&L: ${metrics.total_pnl}")
    logger.info(f"  Win Rate: {metrics.win_rate:.1%}")
    logger.info(f"  Uptime: {metrics.uptime_seconds}s ({metrics.uptime_seconds/60:.1f}m)")
    
    # Serialize to JSON
    import json
    metrics_json = metrics.model_dump_json(indent=2)
    logger.info("\nMetrics as JSON:")
    for line in metrics_json.split('\n')[:10]:
        print(f"  {line}")


async def main():
    """Run all examples."""
    try:
        await example_pydantic_validation()
        print("\n")
        await example_signal_generation()
        print("\n")
        await example_engine_initialization()
        print("\n")
        await example_metrics_tracking()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All examples completed successfully!")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("Trading Engine Examples & Tests")
    logger.info("Python 3.8+ with asyncio")
    
    asyncio.run(main())
