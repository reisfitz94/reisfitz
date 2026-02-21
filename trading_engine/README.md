# Real-Time Event-Driven Trading Engine

A **production-grade** asynchronous trading engine demonstrating advanced Python concepts for financial systems development. This is the "gold standard" project for a financial Python developer.

## 🎯 Key Features

### Advanced Concepts Demonstrated

✅ **Asynchronous Programming (asyncio)**
- Non-blocking concurrent coroutines for handling multiple data feeds
- Proper event loop management and graceful shutdown
- Concurrent task orchestration with `asyncio.gather()`

✅ **WebSocket Real-Time Data**
- Binance spot market data streaming via native WebSocket
- Automatic reconnection with exponential backoff
- Multi-symbol concurrent data handling

✅ **Type Safety & Validation**
- Pydantic models for strict data validation
- Type hints throughout codebase
- Automatic JSON serialization/deserialization

✅ **Async Database Operations**
- SQLite with aiosqlite for non-blocking I/O
- Schema management and migrations
- Efficient persistence of signals and orders

✅ **Real-Time Signal Generation**
- Moving average crossover strategy (Golden Cross/Death Cross)
- O(1) SMA calculation with sliding windows
- Confidence-based signal filtering

✅ **Risk Management**
- Automated stop-loss and take-profit levels
- Position sizing based on account percentage
- Order tracking and execution logging

## 📋 Architecture

```
trading_engine/
├── __init__.py           # Package initialization
├── models.py             # Pydantic data models (type-safe)
├── websocket.py          # Async WebSocket connector (data feed)
├── signals.py            # Technical analysis & signal generation
├── database.py           # Async database operations
├── engine.py             # Core trading engine orchestrator
└── main.py               # Entry point & CLI interface
```

### Component Overview

#### `models.py` - Type-Safe Data Structures
```python
# All models include validation, serialization, and type hints
PriceTick          # Single price update from WebSocket
Candle             # OHLCV candlestick data
TradingSignal      # Generated buy/sell signals
Order              # Executable trading orders
EngineConfig       # Engine configuration
PerformanceMetrics # Trading statistics
```

#### `websocket.py` - Real-Time Data Feed
```python
BinanceWebSocketConnector
├── Auto-reconnection logic (configurable max attempts)
├── Multi-symbol concurrent streaming
├── Callback registration system
└── Proper lifecycle management (context managers)
```

#### `signals.py` - Technical Analysis
```python
SimpleMovingAverage    # Efficient O(1) SMA with deque
SignalGenerator        # Moving average crossover strategy
├── Golden Cross (SMA_short > SMA_long) → BUY
└── Death Cross (SMA_short < SMA_long) → SELL
```

#### `database.py` - Async Persistence
```python
SQLiteBackend
├── Non-blocking I/O with aiosqlite
├── Schema: signals, orders, metrics tables
├── Indexed queries for performance
└── Foreign key relationships
```

#### `engine.py` - Core Orchestration
```python
TradingEngine
├── Coordinates all components
├── Event-driven architecture
├── Order generation and execution
├── Metrics tracking
└── Graceful lifecycle management
```

#### `main.py` - CLI & Monitoring
```python
run_engine()       # Main entry point
demo_mode()        # Safe demo with small positions
EngineDashboard    # Real-time terminal monitoring
```

## 🚀 Quick Start

### Installation

1. **Clone and navigate:**
```bash
cd /workspaces/reisfitz
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Required packages:
- `aiohttp` - Async HTTP/WebSocket client
- `aiosqlite` - Async SQLite driver
- `pydantic` - Data validation and serialization
- `python-dateutil` - Date utilities

### Run Engine

**Start with default settings (BTC + ETH):**
```bash
python -m trading_engine
```

**Run in demo mode (safe defaults):**
```bash
python -m trading_engine --demo
```

**Custom configuration:**
```bash
python -m trading_engine \
    --symbols BTCUSDT ETHUSDT BNBUSDT \
    --sma-short 5 \
    --sma-long 15 \
    --position-size 0.5
```

### CLI Options

```
--symbols BTCUSDT ETHUSDT    Trading pairs to monitor
--sma-short 10               Short moving average period
--sma-long 20                Long moving average period
--position-size 1.0          Position size (% of account)
--db trading_signals.db      Database file path
--no-dashboard               Disable monitoring dashboard
--demo                       Run in demo mode
```

## 💻 Code Examples

### Initialize Engine Programmatically

```python
import asyncio
from trading_engine import TradingEngine, EngineConfig

async def main():
    config = EngineConfig(
        symbols=["BTCUSDT", "ETHUSDT"],
        sma_short_period=10,
        sma_long_period=20,
        position_size_percent=1.0,
        stop_loss_percent=2.0,
        take_profit_percent=5.0
    )
    
    engine = TradingEngine(config)
    await engine.initialize()
    await engine.run()

asyncio.run(main())
```

### Custom Signal Handler

```python
from trading_engine import TradingEngine, EngineConfig

async def custom_handler():
    config = EngineConfig(symbols=["BTCUSDT"])
    engine = TradingEngine(config)
    
    # Access components directly
    signal_gen = engine.signal_gen
    database = engine.database
    
    # Get SMA state for symbol
    state = signal_gen.get_state("btcusdt")
    print(f"Current SMA10: ${state.sma_short}")
    print(f"Current SMA20: ${state.sma_long}")
```

### Query Historical Signals

```python
import asyncio
from trading_engine.database import SQLiteBackend

async def query_signals():
    db = SQLiteBackend()
    
    # Get last 100 BTC signals
    signals = await db.get_signals(symbol="BTCUSDT", limit=100)
    
    for signal in signals:
        print(f"{signal.timestamp} {signal.signal_type.value} @ ${signal.price}")
```

## 🔄 How It Works

### Signal Generation Flow

```
WebSocket Tick → Signal Generator → Database → Order Executor
     ↓                ↓                 ↓           ↓
  Price Update    MA Crossover?    Log Signal   Execute Order
                  Golden/Death      Calculate    Risk Management
                  Cross Detection   Risk Metrics  Update Metrics
```

### Event-Driven Architecture

1. **Real-Time Data**: WebSocket connects to Binance and receives price ticks
2. **Signal Processing**: Moving averages calculated in real-time
3. **Signal Detection**: Crossovers identified (BUY on Golden Cross, SELL on Death Cross)
4. **Order Generation**: Risk parameters calculated automatically
5. **Persistence**: Signals and orders logged to SQLite database
6. **Metrics**: Performance tracked throughout runtime

### Key Design Patterns

**Producer-Consumer**: WebSocket produces ticks → Signal generator consumes
**Observer Pattern**: Callback registration for event handling
**Context Manager**: Safe resource lifecycle management
**Async Context Manager**: `async with` for proper cleanup
**Type Validation**: Pydantic enforces data integrity

## 📊 Monitoring Dashboard

The real-time dashboard displays:

```
================================================================================
📊 TRADING ENGINE DASHBOARD | 2026-02-21 14:35:22
================================================================================
Status: 🟢 CONNECTED
Last Prices: BTCUSDT=$45,234.50, ETHUSDT=$2,567.89

Signals Generated: 12 (7 BUY, 5 SELL)
Orders: 11/12 executed
Failed Orders: 1
Open Positions: 3
Win Rate: 58.3%
Total P&L: $1,245.67

Moving Averages:
  BTCUSDT: SMA10=$45,200.00, SMA20=$45,100.00 📈
  ETHUSDT: SMA10=$2,550.00, SMA20=$2,560.00 📉
================================================================================
```

## 🗄️ Database Schema

### `signals` table
```sql
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- BUY, SELL, HOLD
    price REAL NOT NULL,
    sma_short REAL,
    sma_long REAL,
    timestamp DATETIME NOT NULL,
    confidence REAL NOT NULL,    -- 0.0 to 1.0
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `orders` table
```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_id TEXT,
    signal_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    status TEXT NOT NULL,         -- PENDING, EXECUTED, FAILED
    created_at DATETIME NOT NULL,
    executed_at DATETIME,
    execution_price REAL,
    notes TEXT
);
```

## 🔧 Advanced Configuration

### Risk Management Settings
```python
config = EngineConfig(
    position_size_percent=1.0,      # 1% of account per trade
    stop_loss_percent=2.0,          # 2% below entry
    take_profit_percent=5.0,        # 5% above entry
    risk_management_enabled=True
)
```

### Strategy Parameters
```python
config = EngineConfig(
    sma_short_period=10,    # Fast MA (sensitive to recent price)
    sma_long_period=20      # Slow MA (smoother trend)
)
```

**Faster SMA** (e.g., 5/10): More signals, higher false positives
**Slower SMA** (e.g., 20/50): Fewer signals, robust trends

## 🚨 Error Handling & Resilience

The engine implements robust error handling:

✅ **WebSocket Reconnection**: Auto-reconnect with configurable backoff
✅ **Data Validation**: Pydantic catches malformed data
✅ **Async Error Handling**: try/except in all coroutines
✅ **Graceful Shutdown**: SIGINT (Ctrl+C) handling with cleanup
✅ **Database Resilience**: SQLite transaction management

## 📈 Performance Characteristics

### Computational Complexity
- **SMA Calculation**: O(1) per update (sliding window)
- **Signal Detection**: O(1) per price tick
- **Database Operations**: O(log n) indexed queries
- **Memory Usage**: Constant (deque with fixed maxlen)

### Latency
- WebSocket tick → signal: ~1-10ms (Python overhead)
- Order execution: Immediate (demo), API call latency (production)
- Database persistence: Non-blocking async

## 🔐 Production Considerations

To deploy in production:

1. **Replace Binance with Real Broker**: Connect to Alpaca, Interactive Brokers, etc.
2. **Upgrade Database**: Use PostgreSQL with asyncpg for scalability
3. **Add Authentication**: Secure API keys with environment variables
4. **Implement Proper Order Execution**: Connect to broker order API
5. **Add Monitoring**: Sentry for error tracking, Prometheus for metrics
6. **Risk Controls**: Maximum loss limits, position limits, trading hours filters
7. **Paper Trading**: Test strategies before live trading

## 📚 Tech Stack Summary

| Component | Technology | Why |
|-----------|-----------|-----|
| **Async Runtime** | `asyncio` | Standard Python async library, no external deps |
| **Data Validation** | `Pydantic` | Type-safe, performance-optimized validation |
| **WebSocket** | `aiohttp` | Robust async HTTP client with WebSocket support |
| **Database** | `SQLite + aiosqlite` | Simple local DB, async support, no server required |
| **Data Source** | Binance native WebSocket | Free, no API key needed for price data, reliable |
| **Interface** | CLI with argparse | User-friendly command-line control |

## 🎓 Learning Value

This project demonstrates:

✅ Real-world async Python patterns
✅ Type hints and validation at scale
✅ Event-driven architecture design
✅ Financial system implementation
✅ Database interaction in async context
✅ WebSocket connection management
✅ CLI application development
✅ Error handling and resilience
✅ Performance optimization techniques

## 📝 License

Educational project for demonstrating advanced Python concepts.

## 🤝 Contributing

Suggestions for enhancements:
- Multi-timeframe analysis (5min SMA + 15min SMA)
- Additional indicators (RSI, MACD, Bollinger Bands)
- Portfolio optimization with multiple symbols
- Machine learning signal filtering
- Real broker API integration
- Docker containerization
- Kubernetes deployment manifests

---

**Start your real-time trading engine:**
```bash
python -m trading_engine --demo
```
