"""
Trading Engine - Real-Time Event-Driven Trading System

A production-grade asynchronous trading engine showcasing:
- Real-time WebSocket data streaming
- Type-safe data models with Pydantic
- Async database operations
- Technical indicator calculations
- Automated trading signal generation
"""

__version__ = "1.0.0"
__author__ = "Financial Systems"

from .models import (
    PriceTick,
    Candle,
    TradingSignal,
    Order,
    EngineConfig,
    PerformanceMetrics,
    SignalType,
    OrderStatus
)
from .engine import TradingEngine
from .websocket import BinanceWebSocketConnector
from .signals import SignalGenerator, SimpleMovingAverage
from .database import SQLiteBackend

__all__ = [
    "PriceTick",
    "Candle",
    "TradingSignal",
    "Order",
    "EngineConfig",
    "PerformanceMetrics",
    "SignalType",
    "OrderStatus",
    "TradingEngine",
    "BinanceWebSocketConnector",
    "SignalGenerator",
    "SimpleMovingAverage",
    "SQLiteBackend",
]
