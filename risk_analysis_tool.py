"""
Risk Analysis and Reporting Tool
A comprehensive tool for analyzing large historical trade datasets 
and generating risk reports in Excel and PDF formats.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, List, Optional
import warnings
from scipy import stats
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings('ignore')


class TradeDataGenerator:
    """Generate synthetic large historical trade datasets"""
    
    @staticmethod
    def generate_trades(num_trades: int = 1000000, random_state: int = 42) -> pd.DataFrame:
        """
        Generate large historical trade dataset
        
        Args:
            num_trades: Number of trades to generate
            random_state: Random seed for reproducibility
            
        Returns:
            DataFrame with trade data
        """
        np.random.seed(random_state)
        
        print(f"Generating {num_trades:,} trades...")
        
        # Generate dates (spread over 5 years)
        start_date = datetime(2019, 1, 1)
        dates = [start_date + timedelta(minutes=int(i * 2620/num_trades)) for i in range(num_trades)]
        
        # Generate trade data
        data = {
            'timestamp': dates,
            'symbol': np.random.choice(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'], num_trades),
            'side': np.random.choice(['BUY', 'SELL'], num_trades),
            'quantity': np.random.randint(1, 1000, num_trades),
            'price': np.abs(np.random.normal(100, 25, num_trades)),
            'transaction_cost': np.random.uniform(0.001, 0.01, num_trades),
        }
        
        df = pd.DataFrame(data)
        df['value'] = df['quantity'] * df['price']
        df['net_value'] = df['value'] * (1 + df['transaction_cost'] * 
                                         np.where(df['side'] == 'BUY', 1, -1))
        df['daily_return'] = np.random.normal(0.0005, 0.02, num_trades)
        
        print(f"✓ Generated {len(df):,} trades\n")
        
        return df


class RiskCalculator:
    """Calculate risk metrics from trade data"""
    
    @staticmethod
    def calculate_volatility(returns: np.ndarray, periods_per_year: int = 252) -> float:
        """
        Calculate annualized volatility
        
        Args:
            returns: Array of daily returns
            periods_per_year: Trading periods per year (default: 252 days)
            
        Returns:
            Annualized volatility
        """
        daily_vol = np.std(returns)
        annual_vol = daily_vol * np.sqrt(periods_per_year)
        return annual_vol
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence_level: float = 0.95, 
                      method: str = 'historical') -> float:
        """
        Calculate Value at Risk
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level (default: 95%)
            method: 'historical', 'parametric', or 'cornish_fisher'
            
        Returns:
            Value at Risk
        """
        if method == 'historical':
            return np.quantile(returns, 1 - confidence_level)
        
        elif method == 'parametric':
            # Normal distribution assumption
            mu = np.mean(returns)
            sigma = np.std(returns)
            z_score = stats.norm.ppf(1 - confidence_level)
            return mu + z_score * sigma
        
        elif method == 'cornish_fisher':
            # More accurate for non-normal distributions
            mu = np.mean(returns)
            sigma = np.std(returns)
            skewness = stats.skew(returns)
            kurtosis = stats.kurtosis(returns)
            
            z_score = stats.norm.ppf(1 - confidence_level)
            z_adjusted = z_score + (z_score**2 - 1) * skewness / 6 + \
                        (z_score**3 - 3*z_score) * kurtosis / 24
            
            return mu + z_adjusted * sigma
        
        return None
    
    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall)
        
        Args:
            returns: Array of returns
            confidence_level: Confidence level
            
        Returns:
            CVaR value
        """
        var_value = np.quantile(returns, 1 - confidence_level)
        return np.mean(returns[returns <= var_value])
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe Ratio
        """
        excess_returns = returns - risk_free_rate / 252
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02,
                               target_return: float = 0.0) -> float:
        """
        Calculate Sortino Ratio (downside risk focus)
        
        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate
            target_return: Target return level
            
        Returns:
            Sortino Ratio
        """
        excess_returns = returns - risk_free_rate / 252
        downside = returns[returns < target_return]
        downside_std = np.std(downside) if len(downside) > 0 else np.std(returns)
        
        return np.mean(excess_returns) / downside_std * np.sqrt(252)
    
    @staticmethod
    def calculate_max_drawdown(returns: np.ndarray) -> float:
        """
        Calculate Maximum Drawdown
        
        Args:
            returns: Array of returns
            
        Returns:
            Maximum drawdown percentage
        """
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)
    
    @staticmethod
    def calculate_correlation_matrix(df: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        """
        Calculate correlation matrix between assets
        
        Args:
            df: Trade data
            symbols: List of symbols
            
        Returns:
            Correlation matrix
        """
        returns_dict = {}
        
        for symbol in symbols:
            symbol_data = df[df['symbol'] == symbol]
            if len(symbol_data) > 0:
                returns_dict[symbol] = symbol_data['daily_return'].values
        
        # Pad to same length
        max_len = max(len(v) for v in returns_dict.values())
        for key in returns_dict:
            if len(returns_dict[key]) < max_len:
                returns_dict[key] = np.pad(returns_dict[key], 
                                          (0, max_len - len(returns_dict[key])), 
                                          mode='constant', constant_values=0)
        
        returns_df = pd.DataFrame(returns_dict)
        return returns_df.corr()


class RiskReportGenerator:
    """Generate comprehensive risk reports"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize report generator
        
        Args:
            df: Trade data
        """
        self.df = df
        self.symbols = df['symbol'].unique()
        self.risk_calc = RiskCalculator()
    
    def generate_summary_statistics(self) -> Dict:
        """Generate summary statistics"""
        summary = {
            'Total Trades': len(self.df),
            'Date Range': f"{self.df['timestamp'].min().date()} to {self.df['timestamp'].max().date()}",
            'Total Trade Value': f"${self.df['value'].sum():,.2f}",
            'Average Trade Size': f"${self.df['value'].mean():,.2f}",
            'Number of Symbols': len(self.symbols),
            'Symbols': ', '.join(self.symbols),
        }
        return summary
    
    def generate_risk_metrics(self) -> Dict:
        """Generate comprehensive risk metrics"""
        returns = self.df['daily_return'].values
        
        metrics = {
            'Returns Analysis': {
                'Mean Daily Return': f"{np.mean(returns):.4f}",
                'Median Daily Return': f"{np.median(returns):.4f}",
                'Daily Return Std Dev': f"{np.std(returns):.4f}",
                'Annualized Volatility': f"{self.risk_calc.calculate_volatility(returns):.4f}",
                'Skewness': f"{stats.skew(returns):.4f}",
                'Excess Kurtosis': f"{stats.kurtosis(returns):.4f}",
            },
            'Value at Risk (95%)': {
                'Historical': f"{self.risk_calc.calculate_var(returns, 0.95, 'historical'):.4f}",
                'Parametric': f"{self.risk_calc.calculate_var(returns, 0.95, 'parametric'):.4f}",
                'Cornish-Fisher': f"{self.risk_calc.calculate_var(returns, 0.95, 'cornish_fisher'):.4f}",
                'CVaR (Expected Shortfall)': f"{self.risk_calc.calculate_cvar(returns, 0.95):.4f}",
            },
            'Value at Risk (99%)': {
                'Historical': f"{self.risk_calc.calculate_var(returns, 0.99, 'historical'):.4f}",
                'Parametric': f"{self.risk_calc.calculate_var(returns, 0.99, 'parametric'):.4f}",
                'Cornish-Fisher': f"{self.risk_calc.calculate_var(returns, 0.99, 'cornish_fisher'):.4f}",
                'CVaR (Expected Shortfall)': f"{self.risk_calc.calculate_cvar(returns, 0.99):.4f}",
            },
            'Risk-Adjusted Returns': {
                'Sharpe Ratio': f"{self.risk_calc.calculate_sharpe_ratio(returns):.4f}",
                'Sortino Ratio': f"{self.risk_calc.calculate_sortino_ratio(returns):.4f}",
                'Max Drawdown': f"{self.risk_calc.calculate_max_drawdown(returns):.4f}",
            }
        }
        return metrics
    
    def generate_by_symbol_analysis(self) -> Dict:
        """Generate analysis by symbol"""
        by_symbol = {}
        
        for symbol in self.symbols:
            symbol_data = self.df[self.df['symbol'] == symbol]
            returns = symbol_data['daily_return'].values
            
            by_symbol[symbol] = {
                'Trade Count': len(symbol_data),
                'Total Value': f"${symbol_data['value'].sum():,.2f}",
                'Mean Return': f"{np.mean(returns):.4f}",
                'Volatility': f"{self.risk_calc.calculate_volatility(returns):.4f}",
                'VaR (95%)': f"{self.risk_calc.calculate_var(returns, 0.95):.4f}",
                'Sharpe Ratio': f"{self.risk_calc.calculate_sharpe_ratio(returns):.4f}",
            }
        
        return by_symbol
    
    def export_to_excel(self, filepath: str):
        """Export report to Excel"""
        print(f"Generating Excel report: {filepath}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary tab
            summary = self.generate_summary_statistics()
            summary_df = pd.DataFrame(list(summary.items()), columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Risk metrics tab
            risk_metrics = self.generate_risk_metrics()
            
            row = 0
            ws = writer.sheets['Risk Metrics'] if 'Risk Metrics' in writer.sheets else writer.book.create_sheet('Risk Metrics')
            
            for category, metrics in risk_metrics.items():
                ws[f'A{row+1}'] = category
                row += 1
                for metric, value in metrics.items():
                    ws[f'A{row+1}'] = f"  {metric}"
                    ws[f'B{row+1}'] = value
                    row += 1
                row += 1
            
            # By symbol analysis tab
            by_symbol = self.generate_by_symbol_analysis()
            by_symbol_df = pd.DataFrame(by_symbol).T
            by_symbol_df.to_excel(writer, sheet_name='By Symbol')
            
            # Correlation matrix tab
            correlation = self.risk_calc.calculate_correlation_matrix(self.df, list(self.symbols))
            correlation.to_excel(writer, sheet_name='Correlation')
            
            # Trade data sample
            self.df.head(1000).to_excel(writer, sheet_name='Trade Sample', index=False)
        
        print(f"✓ Excel report saved to {filepath}\n")
    
    def export_to_pdf(self, filepath: str):
        """Export report to PDF"""
        print(f"Generating PDF report: {filepath}")
        
        with PdfPages(filepath) as pdf:
            # Page 1: Title and Summary
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.5, 0.95, 'Risk Analysis Report', 
                    ha='center', fontsize=20, fontweight='bold')
            fig.text(0.5, 0.90, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    ha='center', fontsize=10)
            
            summary = self.generate_summary_statistics()
            y_pos = 0.85
            for key, value in summary.items():
                fig.text(0.1, y_pos, f"{key}:", fontsize=10, fontweight='bold')
                fig.text(0.4, y_pos, str(value), fontsize=10)
                y_pos -= 0.04
            
            # Risk metrics
            risk_metrics = self.generate_risk_metrics()
            y_pos = 0.45
            for category, metrics in risk_metrics.items():
                fig.text(0.1, y_pos, category, fontsize=11, fontweight='bold')
                y_pos -= 0.03
                for metric, value in metrics.items():
                    fig.text(0.15, y_pos, f"{metric}: {value}", fontsize=9, family='monospace')
                    y_pos -= 0.025
                    if y_pos < 0.05:
                        break
                if y_pos < 0.05:
                    break
            
            plt.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2: By Symbol Analysis
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.5, 0.95, 'Analysis by Symbol',
                    ha='center', fontsize=16, fontweight='bold')
            
            by_symbol = self.generate_by_symbol_analysis()
            y_pos = 0.90
            for symbol, metrics in by_symbol.items():
                fig.text(0.1, y_pos, symbol, fontsize=12, fontweight='bold')
                y_pos -= 0.03
                for metric, value in metrics.items():
                    fig.text(0.15, y_pos, f"{metric}: {value}", fontsize=9, family='monospace')
                    y_pos -= 0.025
                y_pos -= 0.02
            
            plt.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 3: Correlation Matrix
            fig, ax = plt.subplots(figsize=(8.5, 11))
            correlation = self.risk_calc.calculate_correlation_matrix(self.df, list(self.symbols))
            
            im = ax.imshow(correlation.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax.set_xticks(np.arange(len(correlation.columns)))
            ax.set_yticks(np.arange(len(correlation.columns)))
            ax.set_xticklabels(correlation.columns)
            ax.set_yticklabels(correlation.columns)
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            
            for i in range(len(correlation.columns)):
                for j in range(len(correlation.columns)):
                    text = ax.text(j, i, f'{correlation.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontsize=10)
            
            ax.set_title('Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
            plt.colorbar(im, ax=ax, label='Correlation')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 4: Visualizations
            fig, axes = plt.subplots(2, 2, figsize=(8.5, 11))
            
            # Returns histogram
            returns = self.df['daily_return'].values
            axes[0, 0].hist(returns, bins=50, color='#1F77B4', alpha=0.7, edgecolor='black')
            axes[0, 0].axvline(np.mean(returns), color='red', linestyle='--', linewidth=2, label='Mean')
            axes[0, 0].set_title('Daily Returns Distribution', fontweight='bold')
            axes[0, 0].set_xlabel('Return')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Cumulative returns by symbol
            legend_items = []
            for symbol in self.symbols[:5]:  # Top 5 symbols
                symbol_data = self.df[self.df['symbol'] == symbol]
                cumulative = np.cumprod(1 + symbol_data['daily_return'].values)
                axes[0, 1].plot(cumulative, label=symbol, alpha=0.7)
            axes[0, 1].set_title('Cumulative Returns by Symbol', fontweight='bold')
            axes[0, 1].set_xlabel('Time')
            axes[0, 1].set_ylabel('Cumulative Return')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
            
            # Trade value distribution
            for symbol in self.symbols:
                symbol_data = self.df[self.df['symbol'] == symbol]
                axes[1, 0].hist(symbol_data['value'], bins=30, alpha=0.5, label=symbol)
            axes[1, 0].set_title('Trade Value Distribution', fontweight='bold')
            axes[1, 0].set_xlabel('Trade Value ($)')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # Volatility by symbol
            volatilities = {}
            for symbol in self.symbols:
                symbol_data = self.df[self.df['symbol'] == symbol]
                vol = self.risk_calc.calculate_volatility(symbol_data['daily_return'].values)
                volatilities[symbol] = vol
            
            axes[1, 1].bar(volatilities.keys(), volatilities.values(), color='#2CA02C', alpha=0.7)
            axes[1, 1].set_title('Volatility by Symbol', fontweight='bold')
            axes[1, 1].set_ylabel('Annual Volatility')
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            plt.setp(axes[1, 1].get_xticklabels(), rotation=45)
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"✓ PDF report saved to {filepath}\n")
    
    def print_summary(self):
        """Print summary to console"""
        print(f"\n{'='*70}")
        print("RISK ANALYSIS SUMMARY")
        print(f"{'='*70}\n")
        
        print("SUMMARY STATISTICS:")
        summary = self.generate_summary_statistics()
        for key, value in summary.items():
            print(f"  {key}: {value}")
        print()
        
        print("OVERALL RISK METRICS:")
        risk_metrics = self.generate_risk_metrics()
        for category, metrics in risk_metrics.items():
            print(f"  {category}:")
            for metric, value in metrics.items():
                print(f"    {metric}: {value}")
        print()
        
        print("BY SYMBOL ANALYSIS:")
        by_symbol = self.generate_by_symbol_analysis()
        print(f"  {'Symbol':<10} {'Trades':<10} {'Volatility':<12} {'Sharpe':<10} {'VaR(95%)':<10}")
        print("  " + "-" * 55)
        for symbol, metrics in by_symbol.items():
            print(f"  {symbol:<10} {metrics['Trade Count']:<10} {metrics['Volatility']:<12} {metrics['Sharpe Ratio']:<10} {metrics['VaR (95%)']:<10}")
        print()


def main():
    """Main function"""
    
    print(f"\n{'='*70}")
    print("RISK ANALYSIS AND REPORTING TOOL")
    print(f"{'='*70}\n")
    
    # Generate large dataset
    generator = TradeDataGenerator()
    df = generator.generate_trades(num_trades=1000000)
    
    print("Trade Data Summary:")
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n")
    
    # Create report generator
    report_gen = RiskReportGenerator(df)
    
    # Print summary
    report_gen.print_summary()
    
    # Export to Excel
    excel_path = '/workspaces/reisfitz/risk_analysis_report.xlsx'
    report_gen.export_to_excel(excel_path)
    
    # Export to PDF
    pdf_path = '/workspaces/reisfitz/risk_analysis_report.pdf'
    report_gen.export_to_pdf(pdf_path)
    
    print(f"{'='*70}")
    print("Risk analysis and reporting complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
