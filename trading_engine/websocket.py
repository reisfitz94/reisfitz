"""
Async WebSocket connector for real-time market data streaming.
Handles connection lifecycle, reconnection, and data parsing.
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Callable, Optional, Set
from contextlib import asynccontextmanager

import aiohttp

from .models import PriceTick, Candle

logger = logging.getLogger(__name__)


class BinanceWebSocketConnector:
    """
    Manages WebSocket connection to Binance for real-time price feeds.
    Implements automatic reconnection and graceful shutdown.
    """
    
    def __init__(
        self,
        symbols: list[str],
        endpoint: str = "wss://stream.binance.com:9443/ws",
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 5
    ):
        """
        Initialize WebSocket connector.
        
        Args:
            symbols: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
            endpoint: Binance WebSocket endpoint
            reconnect_delay: Seconds to wait before reconnection
            max_reconnect_attempts: Maximum reconnection tries before giving up
        """
        self.symbols = {s.lower() for s in symbols}
        self.endpoint = endpoint
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket = None
        self.is_connected = False
        self.reconnect_count = 0
        self.callbacks: list[Callable[[PriceTick], None]] = []
        
    def subscribe_to_ticks(self, callback: Callable[[PriceTick], None]) -> None:
        """Register callback to receive price ticks."""
        self.callbacks.append(callback)
        logger.info(f"Subscribed callback: {callback.__name__}")
    
    async def _build_stream_url(self) -> str:
        """
        Build Binance multi-stream URL.
        
        Format: /stream?streams=btcusdt@ticker/ethusdt@ticker
        Using @ticker for real-time price updates (~1 second interval)
        """
        streams = "/".join([f"{symbol}@ticker" for symbol in self.symbols])
        return f"{self.endpoint}/stream?streams={streams}"
    
    async def _parse_ticker_message(self, data: dict) -> Optional[PriceTick]:
        """
        Parse Binance ticker message into PriceTick.
        
        Binance ticker format includes:
        - c: close price
        - s: symbol
        - E: event time
        - v: total traded base asset volume
        """
        try:
            payload = data.get("data", {})
            if not payload or payload.get("e") != "24hrTicker":
                return None
                
            symbol = payload.get("s", "").lower()
            if symbol not in self.symbols:
                return None
                
            return PriceTick(
                symbol=symbol,
                price=Decimal(str(payload.get("c", 0))),
                timestamp=datetime.fromtimestamp(payload.get("E", 0) / 1000),
                volume=Decimal(str(payload.get("v", 0)))
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing ticker message: {e}")
            return None
    
    async def _on_message(self) -> None:
        """Process incoming WebSocket messages."""
        try:
            async for msg in self.websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        tick = await self._parse_ticker_message(data)
                        
                        if tick:
                            for callback in self.callbacks:
                                try:
                                    await self._call_callback(callback, tick)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}")
                                    
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {e}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.websocket.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.warning("WebSocket connection closed")
                    break
                    
        except asyncio.CancelledError:
            logger.info("Message handler cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in message handler: {e}")
            raise
    
    async def _call_callback(self, callback: Callable, tick: PriceTick) -> None:
        """
        Call callback safely (handles both sync and async callbacks).
        """
        if asyncio.iscoroutinefunction(callback):
            await callback(tick)
        else:
            callback(tick)
    
    async def connect(self) -> None:
        """
        Establish WebSocket connection with automatic reconnection logic.
        """
        stream_url = await self._build_stream_url()
        
        while self.reconnect_count < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to Binance WebSocket (attempt {self.reconnect_count + 1})")
                
                self.session = aiohttp.ClientSession()
                self.websocket = await self.session.ws_connect(
                    stream_url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    heartbeat=30
                )
                
                self.is_connected = True
                self.reconnect_count = 0
                logger.info("WebSocket connected successfully")
                
                await self._on_message()
                
            except asyncio.TimeoutError:
                logger.warning("Connection timeout, reconnecting...")
                self.reconnect_count += 1
                await asyncio.sleep(self.reconnect_delay)
                
            except aiohttp.ClientError as e:
                logger.error(f"Connection error: {e}")
                self.reconnect_count += 1
                await asyncio.sleep(self.reconnect_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.reconnect_count += 1
                await asyncio.sleep(self.reconnect_delay)
                
            finally:
                self.is_connected = False
                if self.websocket:
                    await self.websocket.close()
                if self.session:
                    await self.session.close()
        
        logger.error(f"Failed to connect after {self.max_reconnect_attempts} attempts")
        raise ConnectionError("Max reconnection attempts exceeded")
    
    async def disconnect(self) -> None:
        """Close WebSocket connection gracefully."""
        logger.info("Disconnecting WebSocket")
        
        self.is_connected = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("WebSocket disconnected")
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for WebSocket lifecycle management."""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()
