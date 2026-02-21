"""
Stock Data Analysis Project
A comprehensive Python project for analyzing stock data, calculating volatility, 
and visualizing time-series data using pandas, yfinance, and matplotlib.
"""

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class StockAnalyzer:
    """Analyzes stock data and generates insights"""
    
    def __init__(self, ticker: str, start_date: Optional[str] = None, 
                 end_date: Optional[str] = None, period: str = "1y"):
        """
        Initialize stock analyzer
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            period: Period if dates not specified (e.g., '1y', '6mo', '3mo')
        """
        self.ticker = ticker.upper()
        self.period = period
        self.start_date = start_date
        self.end_date = end_date
        self.df = None
        self.company_info = None
        
        self._fetch_data()
    
    def _fetch_data(self):
        """Fetch stock data from yfinance"""
        try:
            print(f"Fetching data for {self.ticker}...")
            
            if self.start_date and self.end_date:
                self.df = yf.download(self.ticker, start=self.start_date, 
                                     end=self.end_date, progress=False)
            else:
                self.df = yf.download(self.ticker, period=self.period, progress=False)
            
            # Handle multi-index columns case
            if isinstance(self.df.columns, pd.MultiIndex):
                self.df.columns = self.df.columns.get_level_values(0)
            
            # Get company info
            ticker_info = yf.Ticker(self.ticker)
            self.company_info = ticker_info.info
            
            if len(self.df) == 0:
                raise ValueError(f"No data found for ticker {self.ticker}")
            
            print(f"✓ Successfully fetched {len(self.df)} trading days of data\n")
        
        except Exception as e:
            raise ValueError(f"Failed to fetch data: {str(e)}")
    
    def get_summary_stats(self) -> Dict:
        """Calculate summary statistics"""
        if self.df is None:
            return {}
        
        close_prices = self.df['Close']
        
        try:
            company_name = str(self.company_info.get('longName', 'N/A')) if self.company_info else 'N/A'
            sector = str(self.company_info.get('sector', 'N/A')) if self.company_info else 'N/A'
        except:
            company_name = 'N/A'
            sector = 'N/A'
        
        try:
            current_price = float(close_prices.iloc[-1])
            open_price = float(close_prices.iloc[0])
            avg_price = float(close_prices.mean())
            min_price = float(close_prices.min())
            max_price = float(close_prices.max())
            return_pct = ((current_price / open_price - 1) * 100)
        except:
            current_price = open_price = avg_price = min_price = max_price = return_pct = 0
        
        stats = {
            'Ticker': self.ticker,
            'Company': company_name,
            'Sector': sector,
            'Start Date': self.df.index[0].strftime('%Y-%m-%d'),
            'End Date': self.df.index[-1].strftime('%Y-%m-%d'),
            'Total Days': len(self.df),
            'Price Range': f"${min_price:.2f} - ${max_price:.2f}",
            'Current Price': f"${current_price:.2f}",
            'Opening Price': f"${open_price:.2f}",
            'Average Price': f"${avg_price:.2f}",
            'Return %': f"{return_pct:.2f}%",
        }
        
        return stats
    
    def calculate_volatility(self, window: int = 20) -> Dict:
        """
        Calculate various volatility metrics
        
        Args:
            window: Rolling window in days
        
        Returns:
            Dictionary with volatility metrics
        """
        if self.df is None:
            return {}
        
        close_prices = self.df['Close']
        returns = close_prices.pct_change()
        
        # Historical volatility (standard deviation of returns)
        volatility_daily = float(returns.std())
        volatility_annual = volatility_daily * np.sqrt(252)  # 252 trading days per year
        
        # Rolling volatility
        rolling_volatility = returns.rolling(window=window).std()
        
        # Average true range
        high = self.df['High']
        low = self.df['Low']
        tr1 = high - low
        tr2 = abs(high - close_prices.shift())
        tr3 = abs(low - close_prices.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()
        
        metrics = {
            'Daily Volatility': f"{volatility_daily:.4f}",
            'Annual Volatility': f"{volatility_annual:.4f}",
            'Annual Volatility %': f"{volatility_annual * 100:.2f}%",
            'Rolling Volatility (20d) Mean': f"{float(rolling_volatility.mean()):.4f}",
            'Rolling Volatility (20d) Max': f"{float(rolling_volatility.max()):.4f}",
            'ATR (20d) Current': f"{float(atr.iloc[-1]):.2f}",
            'ATR (20d) Average': f"{float(atr.mean()):.2f}",
        }
        
        return metrics
    
    def calculate_technical_indicators(self) -> pd.DataFrame:
        """Calculate technical indicators"""
        if self.df is None:
            return pd.DataFrame()
        
        df = self.df.copy()
        
        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Stochastic Oscillator
        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        return df
    
    def get_returns_analysis(self) -> Dict:
        """Analyze returns distribution"""
        if self.df is None:
            return {}
        
        close_prices = self.df['Close']
        returns = close_prices.pct_change().dropna()
        
        try:
            analysis = {
                'Mean Return': f"{float(returns.mean()):.4f}",
                'Median Return': f"{float(returns.median()):.4f}",
                'Std Dev': f"{float(returns.std()):.4f}",
                'Skewness': f"{float(returns.skew()):.4f}",
                'Kurtosis': f"{float(returns.kurtosis()):.4f}",
                'Min Daily Return': f"{float(returns.min()):.4f}",
                'Max Daily Return': f"{float(returns.max()):.4f}",
                'Value at Risk (95%)': f"{float(returns.quantile(0.05)):.4f}",
                'Sharpe Ratio': f"{float((returns.mean() / returns.std() * np.sqrt(252))):.4f}",
                'Positive Days': f"{(returns > 0).sum()} ({(returns > 0).sum() / len(returns) * 100:.1f}%)",
                'Negative Days': f"{(returns < 0).sum()} ({(returns < 0).sum() / len(returns) * 100:.1f}%)",
            }
            return analysis
        except:
            return {}
    
    def print_analysis_report(self):
        """Print comprehensive analysis report"""
        print(f"\n{'='*70}")
        print(f"STOCK ANALYSIS REPORT - {self.ticker}")
        print(f"{'='*70}\n")
        
        # Summary Statistics
        print(f"{'SUMMARY STATISTICS':-^70}")
        summary = self.get_summary_stats()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print()
        
        # Volatility Analysis
        print(f"{'VOLATILITY ANALYSIS':-^70}")
        volatility = self.calculate_volatility()
        for key, value in volatility.items():
            print(f"  {key}: {value}")
        print()
        
        # Returns Analysis
        print(f"{'RETURNS ANALYSIS':-^70}")
        returns_analysis = self.get_returns_analysis()
        for key, value in returns_analysis.items():
            print(f"  {key}: {value}")
        print()
        
        # Current Technical Indicators
        print(f"{'CURRENT TECHNICAL INDICATORS':-^70}")
        indicators_df = self.calculate_technical_indicators()
        latest = indicators_df.iloc[-1]
        
        print(f"  Price: ${latest['Close']:.2f}")
        print(f"  SMA 20: ${latest['SMA_20']:.2f}")
        print(f"  SMA 50: ${latest['SMA_50']:.2f}")
        print(f"  SMA 200: ${latest['SMA_200']:.2f}")
        print(f"  RSI (14): {latest['RSI']:.2f}")
        print(f"  MACD: {latest['MACD']:.4f}")
        print(f"  Signal Line: {latest['Signal_Line']:.4f}")
        print(f"  Bollinger Upper: ${latest['BB_Upper']:.2f}")
        print(f"  Bollinger Lower: ${latest['BB_Lower']:.2f}")
        print()
        
        print(f"{'='*70}\n")
    
    def plot_price_and_volume(self, figsize: Tuple = (14, 8)):
        """Plot price and trading volume"""
        if self.df is None:
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Price plot
        ax1.plot(self.df.index, self.df['Close'], linewidth=2, color='#2E86AB', label='Close Price')
        ax1.fill_between(self.df.index, self.df['Low'], self.df['High'], 
                         alpha=0.2, color='#2E86AB')
        ax1.set_title(f'{self.ticker} - Price and Volume', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Volume plot
        colors = ['green' if self.df['Close'].iloc[i] >= self.df['Open'].iloc[i] 
                 else 'red' for i in range(len(self.df))]
        ax2.bar(self.df.index, self.df['Volume'], color=colors, alpha=0.6)
        ax2.set_title('Trading Volume', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Volume', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return fig
    
    def plot_moving_averages(self, figsize: Tuple = (14, 7)):
        """Plot price with moving averages"""
        if self.df is None:
            return
        
        indicators_df = self.calculate_technical_indicators()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(indicators_df.index, indicators_df['Close'], linewidth=2, 
               color='#1F77B4', label='Close Price', zorder=3)
        ax.plot(indicators_df.index, indicators_df['SMA_20'], linewidth=1.5, 
               color='#FF7F0E', label='SMA 20', alpha=0.7)
        ax.plot(indicators_df.index, indicators_df['SMA_50'], linewidth=1.5, 
               color='#2CA02C', label='SMA 50', alpha=0.7)
        ax.plot(indicators_df.index, indicators_df['SMA_200'], linewidth=1.5, 
               color='#D62728', label='SMA 200', alpha=0.7)
        
        ax.set_title(f'{self.ticker} - Moving Averages', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Price ($)', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_bollinger_bands(self, figsize: Tuple = (14, 7)):
        """Plot Bollinger Bands"""
        if self.df is None:
            return
        
        indicators_df = self.calculate_technical_indicators()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(indicators_df.index, indicators_df['Close'], linewidth=2, 
               color='#1F77B4', label='Close Price')
        ax.plot(indicators_df.index, indicators_df['BB_Middle'], linewidth=1.5, 
               color='#FF7F0E', label='Middle Band (SMA 20)', linestyle='--', alpha=0.7)
        ax.plot(indicators_df.index, indicators_df['BB_Upper'], linewidth=1, 
               color='#D62728', label='Upper Band (±2σ)', linestyle=':', alpha=0.7)
        ax.plot(indicators_df.index, indicators_df['BB_Lower'], linewidth=1, 
               color='#D62728', label='Lower Band (±2σ)', linestyle=':', alpha=0.7)
        ax.fill_between(indicators_df.index, indicators_df['BB_Upper'], 
                       indicators_df['BB_Lower'], alpha=0.1, color='#D62728')
        
        ax.set_title(f'{self.ticker} - Bollinger Bands', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Price ($)', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_rsi(self, figsize: Tuple = (14, 7)):
        """Plot RSI indicator"""
        if self.df is None:
            return
        
        indicators_df = self.calculate_technical_indicators()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(indicators_df.index, indicators_df['RSI'], linewidth=2, color='#1F77B4')
        ax.axhline(y=70, color='#D62728', linestyle='--', linewidth=1, alpha=0.7, label='Overbought (70)')
        ax.axhline(y=30, color='#2CA02C', linestyle='--', linewidth=1, alpha=0.7, label='Oversold (30)')
        ax.fill_between(indicators_df.index, 30, 70, alpha=0.1, color='#1F77B4')
        
        ax.set_title(f'{self.ticker} - RSI (14)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('RSI', fontsize=11)
        ax.set_ylim([0, 100])
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_macd(self, figsize: Tuple = (14, 7)):
        """Plot MACD indicator"""
        if self.df is None:
            return
        
        indicators_df = self.calculate_technical_indicators()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # MACD line
        ax.plot(indicators_df.index, indicators_df['MACD'], linewidth=2, 
               color='#1F77B4', label='MACD')
        ax.plot(indicators_df.index, indicators_df['Signal_Line'], linewidth=2, 
               color='#FF7F0E', label='Signal Line')
        
        # Histogram
        colors = ['green' if x > 0 else 'red' for x in indicators_df['MACD_Histogram']]
        ax.bar(indicators_df.index, indicators_df['MACD_Histogram'], color=colors, 
              alpha=0.3, label='Histogram')
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title(f'{self.ticker} - MACD', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('MACD Value', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_volatility(self, window: int = 20, figsize: Tuple = (14, 7)):
        """Plot rolling volatility"""
        if self.df is None:
            return
        
        close_prices = self.df['Close']
        returns = close_prices.pct_change()
        rolling_volatility = returns.rolling(window=window).std() * 100
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(rolling_volatility.index, rolling_volatility, linewidth=2, color='#D62728')
        ax.fill_between(rolling_volatility.index, rolling_volatility, alpha=0.3, color='#D62728')
        ax.axhline(y=rolling_volatility.mean(), color='#1F77B4', linestyle='--', 
                  linewidth=2, label=f'Mean ({rolling_volatility.mean():.2f}%)')
        
        ax.set_title(f'{self.ticker} - Rolling Volatility ({window}-day)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Volatility (%)', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_returns_distribution(self, figsize: Tuple = (14, 5)):
        """Plot returns distribution histogram"""
        if self.df is None:
            return
        
        close_prices = self.df['Close']
        returns = close_prices.pct_change().dropna() * 100
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Histogram
        ax1.hist(returns, bins=50, color='#1F77B4', alpha=0.7, edgecolor='black')
        ax1.axvline(returns.mean(), color='#D62728', linestyle='--', linewidth=2, label=f'Mean: {returns.mean():.2f}%')
        ax1.axvline(returns.median(), color='#2CA02C', linestyle='--', linewidth=2, label=f'Median: {returns.median():.2f}%')
        ax1.set_title('Daily Returns Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Daily Return (%)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Q-Q Plot
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal Distribution)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_cumulative_returns(self, figsize: Tuple = (14, 7)):
        """Plot cumulative returns"""
        if self.df is None:
            return
        
        close_prices = self.df['Close']
        returns = close_prices.pct_change()
        cumulative_returns = (1 + returns).cumprod() - 1
        
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(cumulative_returns.index, cumulative_returns * 100, linewidth=2, color='#1F77B4')
        ax.fill_between(cumulative_returns.index, cumulative_returns * 100, alpha=0.3, color='#1F77B4')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        ax.set_title(f'{self.ticker} - Cumulative Returns', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Cumulative Return (%)', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


class PortfolioAnalyzer:
    """Analyze multiple stocks as a portfolio"""
    
    def __init__(self, tickers: List[str], period: str = "1y"):
        """
        Initialize portfolio analyzer
        
        Args:
            tickers: List of stock ticker symbols
            period: Analysis period
        """
        self.tickers = [t.upper() for t in tickers]
        self.period = period
        self.data = {}
        self.correlation_matrix = None
        
        self._fetch_data()
    
    def _fetch_data(self):
        """Fetch data for all tickers"""
        print(f"Fetching data for {len(self.tickers)} stocks...")
        
        for ticker in self.tickers:
            try:
                df = yf.download(ticker, period=self.period, progress=False)
                
                # Handle multi-index columns if needed
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                if len(df) > 0:
                    self.data[ticker] = df
                else:
                    print(f"  ⚠ No data for {ticker}")
            except Exception as e:
                print(f"  ⚠ Failed to fetch {ticker}: {str(e)}")
        
        print(f"✓ Successfully fetched {len(self.data)} stocks\n")
    
    def calculate_correlation(self) -> pd.DataFrame:
        """Calculate correlation matrix between stocks"""
        if not self.data:
            return pd.DataFrame()
        
        close_prices_dict = {}
        for ticker, df in self.data.items():
            close_prices_dict[ticker] = df['Close']
        
        close_prices = pd.DataFrame(close_prices_dict)
        self.correlation_matrix = close_prices.corr()
        return self.correlation_matrix
    
    def plot_correlation_heatmap(self, figsize: Tuple = (10, 8)):
        """Plot correlation heatmap"""
        if self.correlation_matrix is None:
            self.calculate_correlation()
        
        if self.correlation_matrix is None or self.correlation_matrix.empty:
            print("Cannot plot correlation heatmap - no data available")
            return None
        
        fig, ax = plt.subplots(figsize=figsize)
        
        tickers = list(self.correlation_matrix.columns)
        
        im = ax.imshow(self.correlation_matrix.values, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        
        ax.set_xticks(np.arange(len(tickers)))
        ax.set_yticks(np.arange(len(tickers)))
        ax.set_xticklabels(tickers)
        ax.set_yticklabels(tickers)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        for i in range(len(tickers)):
            for j in range(len(tickers)):
                text = ax.text(j, i, f'{self.correlation_matrix.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=10)
        
        ax.set_title('Stock Correlation Matrix', fontsize=14, fontweight='bold')
        plt.colorbar(im, ax=ax, label='Correlation')
        
        plt.tight_layout()
        return fig
    
    def plot_normalized_prices(self, figsize: Tuple = (14, 7)):
        """Plot normalized prices for comparison"""
        fig, ax = plt.subplots(figsize=figsize)
        
        for ticker, df in self.data.items():
            normalized = (df['Close'] / df['Close'].iloc[0] - 1) * 100
            ax.plot(normalized.index, normalized, linewidth=2, label=ticker)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('Normalized Stock Performance', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Return (%)', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


def main():
    """Main function demonstrating stock analysis"""
    
    print(f"\n{'='*70}")
    print("STOCK DATA ANALYSIS PROJECT")
    print(f"{'='*70}\n")
    
    # Single Stock Analysis
    print("1. ANALYZING SINGLE STOCK: Apple (AAPL)\n")
    print("-" * 70)
    
    try:
        analyzer = StockAnalyzer("AAPL", period="6mo")
        analyzer.print_analysis_report()
        
        # Generate visualizations
        print("Generating visualizations...\n")
        
        fig1 = analyzer.plot_price_and_volume()
        fig1.savefig('/workspaces/reisfitz/stock_analysis_01_price_volume.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_01_price_volume.png")
        
        fig2 = analyzer.plot_moving_averages()
        fig2.savefig('/workspaces/reisfitz/stock_analysis_02_moving_averages.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_02_moving_averages.png")
        
        fig3 = analyzer.plot_bollinger_bands()
        fig3.savefig('/workspaces/reisfitz/stock_analysis_03_bollinger_bands.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_03_bollinger_bands.png")
        
        fig4 = analyzer.plot_rsi()
        fig4.savefig('/workspaces/reisfitz/stock_analysis_04_rsi.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_04_rsi.png")
        
        fig5 = analyzer.plot_macd()
        fig5.savefig('/workspaces/reisfitz/stock_analysis_05_macd.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_05_macd.png")
        
        fig6 = analyzer.plot_volatility()
        fig6.savefig('/workspaces/reisfitz/stock_analysis_06_volatility.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_06_volatility.png")
        
        fig7 = analyzer.plot_returns_distribution()
        fig7.savefig('/workspaces/reisfitz/stock_analysis_07_returns_distribution.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_07_returns_distribution.png")
        
        fig8 = analyzer.plot_cumulative_returns()
        fig8.savefig('/workspaces/reisfitz/stock_analysis_08_cumulative_returns.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_08_cumulative_returns.png")
        
    except Exception as e:
        print(f"Error in single stock analysis: {e}")
    
    print()
    
    # Portfolio Analysis
    print("2. ANALYZING PORTFOLIO: Multiple Tech Stocks\n")
    print("-" * 70)
    
    try:
        portfolio = PortfolioAnalyzer(["AAPL", "MSFT", "GOOGL", "TSLA"], period="1y")
        
        correlation = portfolio.calculate_correlation()
        print("Correlation Matrix:")
        print(correlation)
        print()
        
        fig_corr = portfolio.plot_correlation_heatmap()
        fig_corr.savefig('/workspaces/reisfitz/stock_analysis_09_correlation.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_09_correlation.png\n")
        
        fig_norm = portfolio.plot_normalized_prices()
        fig_norm.savefig('/workspaces/reisfitz/stock_analysis_10_normalized.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: stock_analysis_10_normalized.png\n")
        
    except Exception as e:
        print(f"Error in portfolio analysis: {e}")
    
    print(f"{'='*70}")
    print("Analysis Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
