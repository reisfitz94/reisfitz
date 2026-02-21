"""
Signal generation algorithms using technical indicators.
Calculates moving averages and generates buy/sell signals.
"""

import logging
from collections import deque
from decimal import Decimal
from datetime import datetime
from typing import Optional, Deque

from .models import PriceTick, TradingSignal, SignalType, MovingAverageState

logger = logging.getLogger(__name__)


class SimpleMovingAverage:
    """
    Maintains real-time SMA calculation with sliding window.
    Uses deque for O(1) operations.
    """
    
    def __init__(self, period: int):
        """
        Initialize SMA calculator.
        
        Args:
            period: Number of periods for moving average
        """
        if period < 2:
            raise ValueError("Period must be at least 2")
            
        self.period = period
        self.window: Deque[Decimal] = deque(maxlen=period)
        self.sum = Decimal(0)
    
    def update(self, price: Decimal) -> Optional[Decimal]:
        """
        Update with new price, return SMA if ready.
        
        Args:
            price: New price to add to window
            
        Returns:
            Current SMA if window is full, None if warming up
        """
        # Remove oldest value if window is full
        if len(self.window) == self.period:
            self.sum -= self.window[0]
        
        # Add new value
        self.window.append(price)
        self.sum += price
        
        # Return SMA only when window is full
        if len(self.window) == self.period:
            return self.sum / Decimal(self.period)
        
        return None
    
    def is_ready(self) -> bool:
        """Check if SMA has enough data points."""
        return len(self.window) == self.period
    
    @property
    def current_sma(self) -> Optional[Decimal]:
        """Get current SMA value (None if not ready)."""
        if self.is_ready():
            return self.sum / Decimal(self.period)
        return None


class SignalGenerator:
    """
    Generates trading signals based on moving average crossovers.
    Implements classic "Golden Cross" and "Death Cross" strategy.
    """
    
    def __init__(self, sma_short_period: int = 10, sma_long_period: int = 20):
        """
        Initialize signal generator.
        
        Args:
            sma_short_period: Fast-moving average period (default: 10)
            sma_long_period: Slow-moving average period (default: 20)
        """
        self.sma_short_period = sma_short_period
        self.sma_long_period = sma_long_period
        
        # Per-symbol SMA state
        self.sma_states: dict[str, tuple[SimpleMovingAverage, SimpleMovingAverage]] = {}
        self.last_signal_type: dict[str, SignalType] = {}
        
        logger.info(f"SignalGenerator initialized: SMA({sma_short_period}, {sma_long_period})")
    
    def _get_or_create_sma_pair(self, symbol: str) -> tuple[SimpleMovingAverage, SimpleMovingAverage]:
        """Get or create SMA pair for symbol."""
        if symbol not in self.sma_states:
            sma_short = SimpleMovingAverage(self.sma_short_period)
            sma_long = SimpleMovingAverage(self.sma_long_period)
            self.sma_states[symbol] = (sma_short, sma_long)
            self.last_signal_type[symbol] = SignalType.HOLD
        
        return self.sma_states[symbol]
    
    def get_state(self, symbol: str) -> MovingAverageState:
        """Get current moving average state."""
        sma_short, sma_long = self._get_or_create_sma_pair(symbol)
        
        return MovingAverageState(
            symbol=symbol,
            sma_short=sma_short.current_sma,
            sma_long=sma_long.current_sma,
            price=Decimal(0),  # Will be updated
            timestamp=datetime.utcnow()
        )
    
    def generate_signal(self, tick: PriceTick) -> Optional[TradingSignal]:
        """
        Generate trading signal from price tick using MA crossover strategy.
        
        Strategy:
        - BUY: SMA_short crosses above SMA_long (Golden Cross)
        - SELL: SMA_short crosses below SMA_long (Death Cross)
        
        Args:
            tick: Current price tick
            
        Returns:
            TradingSignal if crossover detected, None otherwise
        """
        sma_short, sma_long = self._get_or_create_sma_pair(tick.symbol)
        
        # Update both moving averages
        sma_short.update(tick.price)
        sma_long.update(tick.price)
        
        # Need both SMAs to be ready to generate signal
        if not (sma_short.is_ready() and sma_long.is_ready()):
            return None
        
        short_val = sma_short.current_sma
        long_val = sma_long.current_sma
        previous_signal = self.last_signal_type.get(tick.symbol, SignalType.HOLD)
        
        signal_type = SignalType.HOLD
        reason = ""
        confidence = 0.5
        
        # Detect crossover
        if short_val > long_val and previous_signal != SignalType.BUY:
            signal_type = SignalType.BUY
            reason = f"Golden Cross: SMA{self.sma_short_period} (${short_val:.2f}) > SMA{self.sma_long_period} (${long_val:.2f})"
            confidence = 0.7  # Moderate confidence
            
        elif short_val < long_val and previous_signal != SignalType.SELL:
            signal_type = SignalType.SELL
            reason = f"Death Cross: SMA{self.sma_short_period} (${short_val:.2f}) < SMA{self.sma_long_period} (${long_val:.2f})"
            confidence = 0.7
        
        # Only emit signal on state change
        if signal_type != SignalType.HOLD and signal_type != previous_signal:
            self.last_signal_type[tick.symbol] = signal_type
            
            return TradingSignal(
                symbol=tick.symbol,
                signal_type=signal_type,
                price=tick.price,
                sma_short=short_val,
                sma_long=long_val,
                timestamp=tick.timestamp,
                confidence=confidence,
                reason=reason
            )
        
        return None
