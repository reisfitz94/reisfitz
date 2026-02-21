"""
Main entry point for trading engine.
Orchestrates all components and provides monitoring interface.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List

from .models import EngineConfig
from .engine import TradingEngine

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class EngineDashboard:
    """
    Terminal dashboard for monitoring trading engine.
    Displays real-time metrics and status.
    """
    
    def __init__(self, engine: TradingEngine, update_interval: int = 5):
        """
        Initialize dashboard.
        
        Args:
            engine: Trading engine instance
            update_interval: Seconds between dashboard updates
        """
        self.engine = engine
        self.update_interval = update_interval
    
    async def update_loop(self) -> None:
        """Periodic dashboard update loop."""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                
                state = self.engine.get_state_snapshot()
                self._render_dashboard(state)
            
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
    
    def _render_dashboard(self, state: dict) -> None:
        """Render dashboard to terminal."""
        # Clear screen would require platform-specific code
        # For now, just print separator and status
        
        timestamp = state['timestamp']
        metrics = state['metrics']
        
        print("\n" + "=" * 80)
        print(f"📊 TRADING ENGINE DASHBOARD | {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Connection status
        status = "🟢 CONNECTED" if state['is_connected'] else "🔴 DISCONNECTED"
        print(f"Status: {status}")
        
        # Last prices
        if state['last_prices']:
            print(f"Last Prices: {', '.join(f'{s}=${p:.2f}' for s, p in state['last_prices'].items())}")
        
        # Metrics
        print(f"\nSignals Generated: {metrics['total_signals']} "
              f"({metrics['buy_signals']} BUY, {metrics['sell_signals']} SELL)")
        print(f"Orders: {metrics['executed_orders']}/{metrics['total_orders']} executed")
        if metrics['failed_orders'] > 0:
            print(f"Failed Orders: {metrics['failed_orders']}")
        
        print(f"Open Positions: {state['open_positions']}")
        print(f"Win Rate: {metrics['win_rate']:.1%}")
        print(f"Total P&L: ${float(metrics['total_pnl']):.2f}")
        
        # SMA States
        if state['sma_states']:
            print("\nMoving Averages:")
            for symbol, sma_vals in state['sma_states'].items():
                short = sma_vals['sma_short']
                long = sma_vals['sma_long']
                if short and long:
                    status = "📈" if short > long else "📉"
                    print(f"  {symbol}: SMA10=${short:.2f}, SMA20=${long:.2f} {status}")
        
        print("=" * 80 + "\n")


async def run_engine(
    symbols: List[str] = None,
    sma_short: int = 10,
    sma_long: int = 20,
    enable_dashboard: bool = True,
    **kwargs
) -> None:
    """
    Run trading engine with given configuration.
    
    Args:
        symbols: Trading pairs to monitor (default: ['BTCUSDT'])
        sma_short: Short SMA period
        sma_long: Long SMA period
        enable_dashboard: Display monitoring dashboard
        **kwargs: Additional config parameters
    """
    # Default symbols
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT"]
    
    # Create configuration
    config = EngineConfig(
        symbols=symbols,
        sma_short_period=sma_short,
        sma_long_period=sma_long,
        **kwargs
    )
    
    # Create engine
    engine = TradingEngine(config)
    await engine.initialize()
    
    # Create dashboard if enabled
    dashboard = EngineDashboard(engine) if enable_dashboard else None
    
    # Run tasks concurrently
    tasks = [engine.run()]
    
    if dashboard:
        tasks.append(dashboard.update_loop())
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await engine.shutdown()


async def demo_mode() -> None:
    """
    Run engine in demo mode with safe defaults.
    Uses small position sizes and conservative risk parameters.
    """
    logger.info("Starting engine in DEMO MODE")
    
    config = EngineConfig(
        symbols=["BTCUSDT", "ETHUSDT"],
        sma_short_period=10,
        sma_long_period=20,
        position_size_percent=0.5,  # Small positions
        stop_loss_percent=2.0,
        take_profit_percent=5.0,
        risk_management_enabled=True
    )
    
    engine = TradingEngine(config)
    await engine.initialize()
    
    dashboard = EngineDashboard(engine, update_interval=3)
    
    try:
        await asyncio.gather(
            engine.run(),
            dashboard.update_loop()
        )
    except KeyboardInterrupt:
        logger.info("Demo stopped by user")
    finally:
        await engine.shutdown()


def main():
    """Entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time Event-Driven Trading Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (BTC and ETH)
  python -m trading_engine
  
  # Run with custom symbols
  python -m trading_engine --symbols BTCUSDT ETHUSDT BNBUSDT
  
  # Run demo mode with smaller positions
  python -m trading_engine --demo
  
  # Customize SMA periods
  python -m trading_engine --sma-short 5 --sma-long 15
        """
    )
    
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTCUSDT"],
        help="Trading pairs to monitor (default: BTCUSDT)"
    )
    parser.add_argument(
        "--sma-short",
        type=int,
        default=10,
        help="Short SMA period (default: 10)"
    )
    parser.add_argument(
        "--sma-long",
        type=int,
        default=20,
        help="Long SMA period (default: 20)"
    )
    parser.add_argument(
        "--position-size",
        type=float,
        default=1.0,
        help="Position size as % of account (default: 1.0)"
    )
    parser.add_argument(
        "--db",
        default="trading_signals.db",
        help="Database file path (default: trading_signals.db)"
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable dashboard display"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode (small positions, conservative settings)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Trading Engine v1.0")
    logger.info(f"Symbols: {args.symbols}")
    logger.info(f"SMA Periods: {args.sma_short}/{args.sma_long}")
    
    try:
        if args.demo:
            asyncio.run(demo_mode())
        else:
            asyncio.run(run_engine(
                symbols=args.symbols,
                sma_short=args.sma_short,
                sma_long=args.sma_long,
                position_size_percent=args.position_size,
                db_url=f"sqlite:///{args.db}",
                enable_dashboard=not args.no_dashboard
            ))
    
    except KeyboardInterrupt:
        logger.info("Engine stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
