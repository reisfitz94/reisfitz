"""
Monte Carlo Option Pricing Simulator
A comprehensive Python program for pricing options using Monte Carlo simulation
with Geometric Brownian Motion stock price dynamics.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class GeometricBrownianMotion:
    """Simulate stock price paths using Geometric Brownian Motion"""
    
    def __init__(self, S0: float, mu: float, sigma: float, random_state: int = 42):
        """
        Initialize GBM parameters
        
        Args:
            S0: Initial stock price
            mu: Drift (expected return)
            sigma: Volatility (standard deviation)
            random_state: Random seed for reproducibility
        """
        self.S0 = S0
        self.mu = mu
        self.sigma = sigma
        self.random_state = random_state
        np.random.seed(random_state)
    
    def simulate_path(self, T: float, dt: float = 1/252) -> np.ndarray:
        """
        Simulate a single stock price path
        
        Args:
            T: Time to maturity (in years)
            dt: Time step (default: 1/252 for daily steps)
            
        Returns:
            Array of simulated prices
        """
        # Number of steps
        N = int(T / dt)
        
        # Initialize price path
        path = np.zeros(N + 1)
        path[0] = self.S0
        
        # Generate random increments
        dW = np.random.normal(0, np.sqrt(dt), N)
        
        # Simulate GBM: dS = μS*dt + σS*dW
        for i in range(N):
            path[i + 1] = path[i] * np.exp(
                (self.mu - 0.5 * self.sigma ** 2) * dt + self.sigma * dW[i]
            )
        
        return path
    
    def simulate_paths(self, T: float, num_paths: int, dt: float = 1/252) -> np.ndarray:
        """
        Simulate multiple stock price paths
        
        Args:
            T: Time to maturity (in years)
            num_paths: Number of paths to simulate
            dt: Time step
            
        Returns:
            2D array of shape (num_paths, time_steps)
        """
        N = int(T / dt)
        
        # Initialize paths array
        paths = np.zeros((num_paths, N + 1))
        paths[:, 0] = self.S0
        
        # Generate random increments for all paths
        dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
        
        # Simulate GBM for all paths
        for i in range(N):
            paths[:, i + 1] = paths[:, i] * np.exp(
                (self.mu - 0.5 * self.sigma ** 2) * dt + self.sigma * dW[:, i]
            )
        
        return paths


class EuropeanOption:
    """European option pricing using Monte Carlo simulation"""
    
    def __init__(self, S0: float, K: float, T: float, r: float, sigma: float, 
                 option_type: str = "call"):
        """
        Initialize option parameters
        
        Args:
            S0: Initial stock price
            K: Strike price
            T: Time to maturity (in years)
            r: Risk-free rate
            sigma: Volatility
            option_type: "call" or "put"
        """
        self.S0 = S0
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.option_type = option_type.lower()
        
        # For Monte Carlo, use risk-neutral drift
        self.gbm = GeometricBrownianMotion(S0, r, sigma)
    
    def payoff(self, ST: float) -> float:
        """
        Calculate option payoff at maturity
        
        Args:
            ST: Stock price at maturity
            
        Returns:
            Payoff value
        """
        if self.option_type == "call":
            return max(ST - self.K, 0)
        elif self.option_type == "put":
            return max(self.K - ST, 0)
        else:
            raise ValueError("option_type must be 'call' or 'put'")
    
    def monte_carlo_price(self, num_paths: int = 10000, num_steps: int = 252) -> Tuple[float, float, np.ndarray]:
        """
        Price option using Monte Carlo simulation
        
        Args:
            num_paths: Number of simulation paths
            num_steps: Number of time steps
            
        Returns:
            (option_price, std_error, payoffs)
        """
        dt = self.T / num_steps
        
        # Simulate paths
        paths = self.gbm.simulate_paths(self.T, num_paths, dt)
        
        # Calculate payoff for each path
        payoffs = np.array([self.payoff(path[-1]) for path in paths])
        
        # Discount back to present value
        option_price = np.exp(-self.r * self.T) * np.mean(payoffs)
        
        # Calculate standard error
        std_error = np.exp(-self.r * self.T) * np.std(payoffs) / np.sqrt(num_paths)
        
        return option_price, std_error, payoffs
    
    def black_scholes_price(self) -> float:
        """
        Calculate theoretical price using Black-Scholes formula
        
        Returns:
            Theoretical option price
        """
        from scipy.stats import norm
        
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (
            self.sigma * np.sqrt(self.T)
        )
        d2 = d1 - self.sigma * np.sqrt(self.T)
        
        if self.option_type == "call":
            price = self.S0 * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:  # put
            price = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - self.S0 * norm.cdf(-d1)
        
        return price
    
    def calculate_greeks_monte_carlo(self, num_paths: int = 10000) -> Dict[str, float]:
        """
        Estimate Greeks using finite differences
        
        Args:
            num_paths: Number of simulation paths
            
        Returns:
            Dictionary of Greek values
        """
        # Base price
        price, _, _ = self.monte_carlo_price(num_paths)
        
        # Delta: dPrice/dS
        eps_s = 0.01
        opt_up = EuropeanOption(self.S0 + eps_s, self.K, self.T, self.r, self.sigma, self.option_type)
        price_up, _, _ = opt_up.monte_carlo_price(num_paths)
        delta = (price_up - price) / eps_s
        
        # Gamma: d²Price/dS²
        opt_down = EuropeanOption(self.S0 - eps_s, self.K, self.T, self.r, self.sigma, self.option_type)
        price_down, _, _ = opt_down.monte_carlo_price(num_paths)
        gamma = (price_up - 2 * price + price_down) / (eps_s ** 2)
        
        # Vega: dPrice/dSigma
        eps_v = 0.001
        opt_vega = EuropeanOption(self.S0, self.K, self.T, self.r, self.sigma + eps_v, self.option_type)
        price_vega, _, _ = opt_vega.monte_carlo_price(num_paths)
        vega = (price_vega - price) / eps_v
        
        # Rho: dPrice/dr
        eps_r = 0.001
        opt_rho = EuropeanOption(self.S0, self.K, self.T, self.r + eps_r, self.sigma, self.option_type)
        price_rho, _, _ = opt_rho.monte_carlo_price(num_paths)
        rho = (price_rho - price) / eps_r
        
        # Theta: -dPrice/dT (approximate)
        eps_t = 0.01 / 252
        opt_theta = EuropeanOption(self.S0, self.K, self.T - eps_t, self.r, self.sigma, self.option_type)
        price_theta, _, _ = opt_theta.monte_carlo_price(num_paths)
        theta = (price - price_theta) / eps_t
        
        return {
            'Delta': delta,
            'Gamma': gamma,
            'Vega': vega,
            'Rho': rho,
            'Theta': theta
        }


class AmericanOption:
    """American option pricing using Monte Carlo with Least Squares method"""
    
    def __init__(self, S0: float, K: float, T: float, r: float, sigma: float,
                 option_type: str = "call"):
        """Initialize American option parameters"""
        self.S0 = S0
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.option_type = option_type.lower()
        self.gbm = GeometricBrownianMotion(S0, r, sigma)
    
    def payoff(self, S: np.ndarray) -> np.ndarray:
        """Calculate option payoff"""
        if self.option_type == "call":
            return np.maximum(S - self.K, 0)
        else:
            return np.maximum(self.K - S, 0)
    
    def least_squares_price(self, num_paths: int = 10000, num_steps: int = 100) -> Tuple[float, float]:
        """
        Price American option using Least Squares Monte Carlo
        
        Args:
            num_paths: Number of simulation paths
            num_steps: Number of time steps
            
        Returns:
            (option_price, std_error)
        """
        dt = self.T / num_steps
        
        # Simulate paths
        paths = self.gbm.simulate_paths(self.T, num_paths, dt)
        
        # Initialize cash flows and values
        cash_flows = np.zeros_like(paths)
        
        # Backward induction from maturity
        # At maturity, payoff is the exercise value
        cash_flows[:, -1] = self.payoff(paths[:, -1])
        
        # Work backwards through time
        for t in range(num_steps - 1, 0, -1):
            # Discount future cash flows
            discount = np.exp(-self.r * dt)
            future_cf = cash_flows[:, t + 1] * discount if t < num_steps else self.payoff(paths[:, t])
            
            # Intrinsic value (immediate exercise value)
            intrinsic = self.payoff(paths[:, t])
            
            # Only consider in-the-money paths for regression
            itm = intrinsic > 0
            
            if np.sum(itm) > 0:
                # Fit polynomial to estimate continuation value
                X = paths[itm, t]
                Y = future_cf[itm]
                
                # Fit polynomial (up to degree 2)
                coeffs = np.polyfit(X, Y, 2)
                continuation_value = np.polyval(coeffs, X)
                
                # Exercise if intrinsic > continuation value
                exercise = intrinsic[itm] > continuation_value
                
                cash_flows[itm, t] = np.where(
                    exercise,
                    intrinsic[itm],
                    future_cf[itm]
                )
                cash_flows[~itm, t] = future_cf[~itm]
            else:
                cash_flows[:, t] = future_cf
        
        # Discount to present
        option_price = np.mean(cash_flows[:, 1]) * np.exp(-self.r * dt)
        std_error = np.std(cash_flows[:, 1]) / np.sqrt(num_paths) * np.exp(-self.r * dt)
        
        return option_price, std_error


class MonteCarloVisualizer:
    """Visualization utilities for Monte Carlo simulations"""
    
    @staticmethod
    def plot_price_paths(paths: np.ndarray, S0: float, num_paths_to_plot: int = 100,
                        figsize: Tuple = (12, 6)):
        """Plot simulated stock price paths"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot subset of paths
        indices = np.random.choice(len(paths), min(num_paths_to_plot, len(paths)), replace=False)
        
        for i in indices:
            ax.plot(paths[i], alpha=0.1, color='#1F77B4')
        
        # Plot mean path
        mean_path = np.mean(paths, axis=0)
        ax.plot(mean_path, linewidth=2, color='#FF7F0E', label='Mean Path')
        
        # Plot initial price
        ax.axhline(y=S0, color='green', linestyle='--', linewidth=2, label='Initial Price')
        
        ax.set_xlabel('Time Steps', fontsize=11)
        ax.set_ylabel('Stock Price ($)', fontsize=11)
        ax.set_title('Geometric Brownian Motion: Simulated Stock Price Paths', 
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def plot_final_distribution(final_prices: np.ndarray, figsize: Tuple = (12, 5)):
        """Plot distribution of final stock prices"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Histogram
        ax1.hist(final_prices, bins=50, color='#1F77B4', alpha=0.7, edgecolor='black')
        ax1.axvline(np.mean(final_prices), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: ${np.mean(final_prices):.2f}')
        ax1.axvline(np.median(final_prices), color='green', linestyle='--', linewidth=2,
                   label=f'Median: ${np.median(final_prices):.2f}')
        ax1.set_xlabel('Stock Price at Maturity ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Distribution of Final Stock Prices', fontsize=11, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Log returns histogram
        log_returns = np.log(final_prices / final_prices[0])
        ax2.hist(log_returns, bins=50, color='#FF7F0E', alpha=0.7, edgecolor='black')
        ax2.axvline(np.mean(log_returns), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(log_returns):.4f}')
        ax2.set_xlabel('Log Returns', fontsize=11)
        ax2.set_ylabel('Frequency', fontsize=11)
        ax2.set_title('Distribution of Log Returns', fontsize=11, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def plot_payoff_distribution(payoffs: np.ndarray, option_type: str, figsize: Tuple = (12, 5)):
        """Plot option payoff distribution"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Payoff histogram
        non_zero = payoffs[payoffs > 0]
        ax1.hist(payoffs, bins=50, color='#2CA02C', alpha=0.7, edgecolor='black')
        ax1.axvline(np.mean(payoffs), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: ${np.mean(payoffs):.2f}')
        ax1.set_xlabel('Payoff ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title(f'{option_type.upper()} Option Payoff Distribution', 
                     fontsize=11, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Statistics
        ax2.axis('off')
        stats_text = f"""
        Total Simulations: {len(payoffs):,}
        In-the-Money (ITM): {len(non_zero):,} ({len(non_zero)/len(payoffs)*100:.2f}%)
        Out-of-Money (OTM): {len(payoffs)-len(non_zero):,} ({(len(payoffs)-len(non_zero))/len(payoffs)*100:.2f}%)
        
        Average Payoff: ${np.mean(payoffs):.2f}
        Median Payoff: ${np.median(payoffs):.2f}
        Max Payoff: ${np.max(payoffs):.2f}
        Min Payoff: ${np.min(payoffs):.2f}
        Std Dev: ${np.std(payoffs):.2f}
        """
        ax2.text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def plot_convergence(prices: List[float], num_paths_range: List[int], 
                        theoretical_price: float, figsize: Tuple = (10, 6)):
        """Plot convergence of Monte Carlo estimate to theoretical value"""
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(num_paths_range, prices, 'o-', linewidth=2, markersize=8, 
               color='#1F77B4', label='MC Estimate')
        ax.axhline(y=theoretical_price, color='red', linestyle='--', linewidth=2,
                  label=f'Theoretical ({theoretical_price:.4f})')
        
        ax.set_xlabel('Number of Paths', fontsize=11)
        ax.set_ylabel('Option Price ($)', fontsize=11)
        ax.set_title('Monte Carlo Convergence to Theoretical Price', 
                    fontsize=12, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        
        plt.tight_layout()
        return fig


def main():
    """Main function demonstrating Monte Carlo option pricing"""
    
    print(f"\n{'='*70}")
    print("MONTE CARLO OPTION PRICING SIMULATOR")
    print(f"{'='*70}\n")
    
    # Option parameters
    S0 = 100.0          # Initial stock price
    K = 105.0           # Strike price
    T = 1.0             # Time to maturity (1 year)
    r = 0.05            # Risk-free rate
    sigma = 0.20        # Volatility (20%)
    num_paths = 50000   # Number of simulation paths
    
    print("OPTION PARAMETERS:")
    print(f"  Initial Stock Price: ${S0:.2f}")
    print(f"  Strike Price: ${K:.2f}")
    print(f"  Time to Maturity: {T} year(s)")
    print(f"  Risk-free Rate: {r*100:.2f}%")
    print(f"  Volatility: {sigma*100:.2f}%")
    print(f"  Number of Paths: {num_paths:,}\n")
    
    # ========== EUROPEAN CALL OPTION ==========
    print("-" * 70)
    print("EUROPEAN CALL OPTION")
    print("-" * 70 + "\n")
    
    call_option = EuropeanOption(S0, K, T, r, sigma, option_type="call")
    
    # Monte Carlo pricing
    call_price_mc, call_std, call_payoffs = call_option.monte_carlo_price(num_paths)
    
    # Black-Scholes pricing
    call_price_bs = call_option.black_scholes_price()
    
    print(f"Monte Carlo Price: ${call_price_mc:.4f} (±${call_std:.4f})")
    print(f"Black-Scholes Price: ${call_price_bs:.4f}")
    print(f"Difference: ${abs(call_price_mc - call_price_bs):.4f} ({abs(call_price_mc - call_price_bs)/call_price_bs*100:.2f}%)\n")
    
    # Greeks
    print("Option Greeks (Finite Differences):")
    call_greeks = call_option.calculate_greeks_monte_carlo(num_paths)
    for greek, value in call_greeks.items():
        print(f"  {greek}: {value:.6f}")
    print()
    
    # ========== EUROPEAN PUT OPTION ==========
    print("-" * 70)
    print("EUROPEAN PUT OPTION")
    print("-" * 70 + "\n")
    
    put_option = EuropeanOption(S0, K, T, r, sigma, option_type="put")
    
    # Monte Carlo pricing
    put_price_mc, put_std, put_payoffs = put_option.monte_carlo_price(num_paths)
    
    # Black-Scholes pricing
    put_price_bs = put_option.black_scholes_price()
    
    print(f"Monte Carlo Price: ${put_price_mc:.4f} (±${put_std:.4f})")
    print(f"Black-Scholes Price: ${put_price_bs:.4f}")
    print(f"Difference: ${abs(put_price_mc - put_price_bs):.4f} ({abs(put_price_mc - put_price_bs)/put_price_bs*100:.2f}%)\n")
    
    # Greeks
    print("Option Greeks (Finite Differences):")
    put_greeks = put_option.calculate_greeks_monte_carlo(num_paths)
    for greek, value in put_greeks.items():
        print(f"  {greek}: {value:.6f}")
    print()
    
    # ========== AMERICAN PUT OPTION ==========
    print("-" * 70)
    print("AMERICAN PUT OPTION (Least Squares MC)")
    print("-" * 70 + "\n")
    
    american_put = AmericanOption(S0, K, T, r, sigma, option_type="put")
    american_price, american_std = american_put.least_squares_price(num_paths)
    
    print(f"American Put Price: ${american_price:.4f} (±${american_std:.4f})")
    print(f"European Put Price: ${put_price_mc:.4f}")
    print(f"Early Exercise Premium: ${american_price - put_price_mc:.4f}\n")
    
    # ========== CONVERGENCE ANALYSIS ==========
    print("-" * 70)
    print("CONVERGENCE ANALYSIS")
    print("-" * 70 + "\n")
    
    path_ranges = [100, 500, 1000, 5000, 10000, 50000]
    call_prices = []
    
    for num_p in path_ranges:
        price, _, _ = call_option.monte_carlo_price(num_p)
        call_prices.append(price)
        print(f"  {num_p:6,} paths: ${price:.4f}")
    
    print(f"  Black-Scholes: ${call_price_bs:.4f}\n")
    
    # ========== VISUALIZATIONS ==========
    print("Generating visualizations...\n")
    
    # Simulate paths for visualization
    gbm = GeometricBrownianMotion(S0, r, sigma)
    paths = gbm.simulate_paths(T, 1000)
    
    # Plot 1: Price paths
    fig1 = MonteCarloVisualizer.plot_price_paths(paths, S0)
    fig1.savefig('/workspaces/reisfitz/monte_carlo_01_price_paths.png', dpi=100, bbox_inches='tight')
    print("✓ Saved: monte_carlo_01_price_paths.png")
    
    # Plot 2: Final price distribution
    fig2 = MonteCarloVisualizer.plot_final_distribution(paths[:, -1])
    fig2.savefig('/workspaces/reisfitz/monte_carlo_02_final_distribution.png', dpi=100, bbox_inches='tight')
    print("✓ Saved: monte_carlo_02_final_distribution.png")
    
    # Plot 3: Call payoff distribution
    fig3 = MonteCarloVisualizer.plot_payoff_distribution(call_payoffs, "call")
    fig3.savefig('/workspaces/reisfitz/monte_carlo_03_call_payoff.png', dpi=100, bbox_inches='tight')
    print("✓ Saved: monte_carlo_03_call_payoff.png")
    
    # Plot 4: Put payoff distribution
    fig4 = MonteCarloVisualizer.plot_payoff_distribution(put_payoffs, "put")
    fig4.savefig('/workspaces/reisfitz/monte_carlo_04_put_payoff.png', dpi=100, bbox_inches='tight')
    print("✓ Saved: monte_carlo_04_put_payoff.png")
    
    # Plot 5: Convergence
    fig5 = MonteCarloVisualizer.plot_convergence(call_prices, path_ranges, call_price_bs)
    fig5.savefig('/workspaces/reisfitz/monte_carlo_05_convergence.png', dpi=100, bbox_inches='tight')
    print("✓ Saved: monte_carlo_05_convergence.png")
    
    print()
    print(f"{'='*70}")
    print("Simulation Complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
