"""
Async database operations for signal and order persistence.
Supports SQLite (aiosqlite) and PostgreSQL (asyncpg).
"""

import logging
import sqlite3
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from abc import ABC, abstractmethod

import aiosqlite

from .models import TradingSignal, Order, OrderStatus

logger = logging.getLogger(__name__)


class DatabaseBackend(ABC):
    """Abstract base for database backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database schema."""
        pass
    
    @abstractmethod
    async def save_signal(self, signal: TradingSignal) -> str:
        """Save signal to database, return signal ID."""
        pass
    
    @abstractmethod
    async def save_order(self, order: Order) -> str:
        """Save order to database, return order ID."""
        pass
    
    @abstractmethod
    async def get_signals(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradingSignal]:
        """Retrieve signals from database."""
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """Retrieve orders from database."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connection."""
        pass


class SQLiteBackend(DatabaseBackend):
    """SQLite async backend using aiosqlite."""
    
    def __init__(self, db_path: str = "trading_engine.db"):
        """
        Initialize SQLite backend.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
    
    async def initialize(self) -> None:
        """Create database and schema."""
        self.db = await aiosqlite.connect(self.db_path)
        
        # Enable foreign keys
        await self.db.execute("PRAGMA foreign_keys = ON")
        
        # Create signals table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                price REAL NOT NULL,
                sma_short REAL,
                sma_long REAL,
                timestamp DATETIME NOT NULL,
                confidence REAL NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_symbol (symbol),
                INDEX idx_timestamp (timestamp)
            )
        """)
        
        # Create orders table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_id TEXT,
                signal_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                executed_at DATETIME,
                execution_price REAL,
                notes TEXT,
                FOREIGN KEY (signal_id) REFERENCES signals(id),
                INDEX idx_symbol (symbol),
                INDEX idx_status (status),
                INDEX idx_created (created_at)
            )
        """)
        
        # Create performance metrics table
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_signals INTEGER,
                buy_signals INTEGER,
                sell_signals INTEGER,
                total_orders INTEGER,
                executed_orders INTEGER,
                failed_orders INTEGER,
                total_pnl REAL,
                win_rate REAL,
                uptime_seconds INTEGER
            )
        """)
        
        await self.db.commit()
        logger.info(f"SQLite database initialized at {self.db_path}")
    
    async def save_signal(self, signal: TradingSignal) -> str:
        """Save signal to database."""
        import uuid
        signal_id = str(uuid.uuid4())
        
        await self.db.execute(
            """
            INSERT INTO signals 
            (id, symbol, signal_type, price, sma_short, sma_long, timestamp, confidence, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                signal.symbol.upper(),
                signal.signal_type.value,
                float(signal.price),
                float(signal.sma_short) if signal.sma_short else None,
                float(signal.sma_long) if signal.sma_long else None,
                signal.timestamp.isoformat(),
                float(signal.confidence),
                signal.reason
            )
        )
        
        await self.db.commit()
        logger.info(f"Signal saved: {signal_id} ({signal.symbol} {signal.signal_type.value})")
        
        return signal_id
    
    async def save_order(self, order: Order) -> str:
        """Save order to database."""
        await self.db.execute(
            """
            INSERT INTO orders
            (id, symbol, signal_id, signal_type, quantity, entry_price, stop_loss, 
             take_profit, status, created_at, executed_at, execution_price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order.order_id,
                order.symbol.upper(),
                order.signal_id,
                order.signal_type.value,
                float(order.quantity),
                float(order.entry_price),
                float(order.stop_loss) if order.stop_loss else None,
                float(order.take_profit) if order.take_profit else None,
                order.status.value,
                order.created_at.isoformat(),
                order.executed_at.isoformat() if order.executed_at else None,
                float(order.execution_price) if order.execution_price else None,
                order.notes
            )
        )
        
        await self.db.commit()
        logger.info(f"Order saved: {order.order_id} ({order.symbol})")
        
        return order.order_id
    
    async def update_order(self, order: Order) -> None:
        """Update order status and execution details."""
        await self.db.execute(
            """
            UPDATE orders
            SET status = ?, executed_at = ?, execution_price = ?, notes = ?
            WHERE id = ?
            """,
            (
                order.status.value,
                order.executed_at.isoformat() if order.executed_at else None,
                float(order.execution_price) if order.execution_price else None,
                order.notes,
                order.order_id
            )
        )
        
        await self.db.commit()
        logger.info(f"Order updated: {order.order_id} → {order.status.value}")
    
    async def get_signals(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradingSignal]:
        """Retrieve signals from database."""
        query = "SELECT * FROM signals"
        params = []
        
        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol.upper())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        signals = []
        for row in rows:
            signals.append(TradingSignal(
                symbol=row[1],
                signal_type=row[2],
                price=Decimal(str(row[3])),
                sma_short=Decimal(str(row[4])) if row[4] else None,
                sma_long=Decimal(str(row[5])) if row[5] else None,
                timestamp=datetime.fromisoformat(row[6]),
                confidence=row[7],
                reason=row[8]
            ))
        
        return signals
    
    async def get_orders(self, symbol: Optional[str] = None, limit: int = 100) -> List[Order]:
        """Retrieve orders from database."""
        query = "SELECT * FROM orders"
        params = []
        
        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol.upper())
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append(Order(
                order_id=row[0],
                symbol=row[1],
                signal_id=row[2],
                signal_type=row[3],
                quantity=Decimal(str(row[4])),
                entry_price=Decimal(str(row[5])),
                stop_loss=Decimal(str(row[6])) if row[6] else None,
                take_profit=Decimal(str(row[7])) if row[7] else None,
                status=row[8],
                created_at=datetime.fromisoformat(row[9]),
                executed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                execution_price=Decimal(str(row[11])) if row[11] else None,
                notes=row[12]
            ))
        
        return orders
    
    async def save_metrics(self, metrics_dict: dict) -> None:
        """Save performance metrics snapshot."""
        await self.db.execute(
            """
            INSERT INTO performance_metrics
            (total_signals, buy_signals, sell_signals, total_orders, executed_orders,
             failed_orders, total_pnl, win_rate, uptime_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metrics_dict.get('total_signals', 0),
                metrics_dict.get('buy_signals', 0),
                metrics_dict.get('sell_signals', 0),
                metrics_dict.get('total_orders', 0),
                metrics_dict.get('executed_orders', 0),
                metrics_dict.get('failed_orders', 0),
                metrics_dict.get('total_pnl', 0),
                metrics_dict.get('win_rate', 0),
                metrics_dict.get('uptime_seconds', 0)
            )
        )
        
        await self.db.commit()
    
    async def close(self) -> None:
        """Close database connection."""
        if self.db:
            await self.db.close()
            logger.info("Database connection closed")
