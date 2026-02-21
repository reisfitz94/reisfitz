"""
Financial Machine Learning Project
A comprehensive project for fraud detection and cash flow forecasting 
using machine learning algorithms.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Tuple, List, Dict
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score, roc_curve,
    precision_recall_curve, f1_score, accuracy_score, mean_squared_error, 
    mean_absolute_error, r2_score
)
from sklearn.preprocessing import PolynomialFeatures
import warnings

warnings.filterwarnings('ignore')


class FraudDetectionModel:
    """Machine learning model for financial fraud detection"""
    
    def __init__(self, random_state: int = 42):
        """Initialize fraud detection model"""
        self.random_state = random_state
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.models = {}
        self.scaler = StandardScaler()
        self.results = {}
    
    def generate_transaction_data(self, n_samples: int = 5000) -> pd.DataFrame:
        """
        Generate synthetic transaction data for fraud detection
        
        Args:
            n_samples: Number of transactions to generate
            
        Returns:
            DataFrame with transaction features
        """
        np.random.seed(self.random_state)
        
        # Generate features
        data = {
            'transaction_amount': np.random.exponential(100, n_samples),
            'transaction_hour': np.random.randint(0, 24, n_samples),
            'merchant_risk_score': np.random.uniform(0, 10, n_samples),
            'days_since_last_transaction': np.random.exponential(5, n_samples),
            'avg_transaction_amount': np.random.exponential(95, n_samples),
            'transaction_frequency': np.random.poisson(3, n_samples),
            'card_age_months': np.random.exponential(24, n_samples),
            'foreign_transaction': np.random.binomial(1, 0.15, n_samples),
            'failed_attempts': np.random.poisson(0.5, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        # Generate fraud labels with realistic patterns
        fraud_probability = (
            0.002 +  # Base fraud rate
            0.01 * (df['transaction_amount'] > df['avg_transaction_amount'] * 3) +
            0.05 * (df['merchant_risk_score'] > 7) +
            0.03 * df['foreign_transaction'] +
            0.02 * (df['failed_attempts'] > 2)
        )
        
        df['is_fraud'] = (np.random.random(n_samples) < fraud_probability).astype(int)
        
        return df
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess and split data"""
        X = df.drop('is_fraud', axis=1)
        y = df['is_fraud']
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.3, random_state=self.random_state, stratify=y
        )
        
        # Scale features
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        
        return self.X_train_scaled, self.X_test_scaled
    
    def train_models(self):
        """Train multiple fraud detection models"""
        print("Training fraud detection models...\n")
        
        # Logistic Regression
        print("  • Training Logistic Regression...")
        lr_model = LogisticRegression(random_state=self.random_state, max_iter=1000)
        lr_model.fit(self.X_train_scaled, self.y_train)
        self.models['Logistic Regression'] = lr_model
        
        # Random Forest
        print("  • Training Random Forest...")
        rf_model = RandomForestClassifier(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        rf_model.fit(self.X_train, self.y_train)
        self.models['Random Forest'] = rf_model
        
        # Gradient Boosting
        print("  • Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(n_estimators=100, random_state=self.random_state)
        gb_model.fit(self.X_train, self.y_train)
        self.models['Gradient Boosting'] = gb_model
        
        print("✓ Models trained\n")
    
    def evaluate_models(self) -> Dict:
        """Evaluate all trained models"""
        print("Evaluating models...\n")
        results = {}
        
        for model_name, model in self.models.items():
            print(f"  {model_name}:")
            
            # Get predictions
            if model_name == 'Logistic Regression':
                y_pred = model.predict(self.X_test_scaled)
                y_pred_proba = model.predict_proba(self.X_test_scaled)[:, 1]
            else:
                y_pred = model.predict(self.X_test)
                y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            precision = np.mean([np.mean(self.y_test[y_pred == 1] == 1) if sum(y_pred == 1) > 0 else 0])
            recall = np.mean([np.mean(self.y_test[y_pred == 1] == 1) if sum(self.y_test == 1) > 0 else 0])
            auc_score = roc_auc_score(self.y_test, y_pred_proba) if len(np.unique(self.y_test)) > 1 else 0
            f1 = f1_score(self.y_test, y_pred, zero_division=0)
            
            results[model_name] = {
                'accuracy': accuracy,
                'auc_score': auc_score,
                'f1_score': f1,
                'y_pred': y_pred,
                'y_pred_proba': y_pred_proba
            }
            
            print(f"    Accuracy: {accuracy:.4f}")
            print(f"    AUC Score: {auc_score:.4f}")
            print(f"    F1 Score: {f1:.4f}")
            print()
        
        self.results = results
        return results
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance from tree-based models"""
        importance = {}
        feature_names = self.X_train.columns
        
        for model_name in ['Random Forest', 'Gradient Boosting']:
            if model_name in self.models:
                model = self.models[model_name]
                importances = model.feature_importances_
                importance[model_name] = dict(zip(feature_names, importances))
        
        return importance
    
    def plot_roc_curves(self, figsize: Tuple = (14, 5)):
        """Plot ROC curves for all models"""
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        for idx, (model_name, model) in enumerate(self.models.items()):
            ax = axes[idx]
            
            # Get predictions
            if model_name == 'Logistic Regression':
                y_pred_proba = model.predict_proba(self.X_test_scaled)[:, 1]
            else:
                y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            
            # Plot ROC curve
            fpr, tpr, _ = roc_curve(self.y_test, y_pred_proba)
            auc = self.results[model_name]['auc_score']
            
            ax.plot(fpr, tpr, color='#1F77B4', linewidth=2, label=f'AUC = {auc:.4f}')
            ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
            
            ax.set_xlabel('False Positive Rate', fontsize=10)
            ax.set_ylabel('True Positive Rate', fontsize=10)
            ax.set_title(f'{model_name} - ROC Curve', fontsize=11, fontweight='bold')
            ax.legend(loc='lower right')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_confusion_matrices(self, figsize: Tuple = (14, 4)):
        """Plot confusion matrices for all models"""
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        
        for idx, (model_name, model) in enumerate(self.models.items()):
            ax = axes[idx]
            
            # Get predictions
            if model_name == 'Logistic Regression':
                y_pred = model.predict(self.X_test_scaled)
            else:
                y_pred = model.predict(self.X_test)
            
            # Plot confusion matrix
            cm = confusion_matrix(self.y_test, y_pred)
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, 
                       cbar=False, annot_kws={'size': 12})
            
            ax.set_xlabel('Predicted', fontsize=10)
            ax.set_ylabel('Actual', fontsize=10)
            ax.set_title(f'{model_name} - Confusion Matrix', fontsize=11, fontweight='bold')
            ax.set_xticklabels(['No Fraud', 'Fraud'])
            ax.set_yticklabels(['No Fraud', 'Fraud'])
        
        plt.tight_layout()
        return fig
    
    def plot_feature_importance(self, figsize: Tuple = (14, 6)):
        """Plot feature importance"""
        importance = self.get_feature_importance()
        
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        for idx, (model_name, features) in enumerate(importance.items()):
            ax = axes[idx]
            
            # Sort features by importance
            features_sorted = dict(sorted(features.items(), key=lambda x: x[1], reverse=True))
            
            # Plot
            colors = plt.cm.viridis(np.linspace(0, 1, len(features_sorted)))
            ax.barh(list(features_sorted.keys()), list(features_sorted.values()), color=colors)
            
            ax.set_xlabel('Importance', fontsize=10)
            ax.set_title(f'{model_name} - Feature Importance', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig


class CashFlowForecastingModel:
    """Machine learning model for cash flow forecasting"""
    
    def __init__(self, random_state: int = 42):
        """Initialize cash flow forecasting model"""
        self.random_state = random_state
        self.models = {}
        self.scaler = StandardScaler()
        self.results = {}
    
    def generate_cashflow_data(self, n_months: int = 48) -> pd.DataFrame:
        """
        Generate synthetic cash flow data
        
        Args:
            n_months: Number of months to generate
            
        Returns:
            DataFrame with monthly cash flows
        """
        np.random.seed(self.random_state)
        
        dates = [datetime(2022, 1, 1) + timedelta(days=30*i) for i in range(n_months)]
        
        # Generate cash flows with trend and seasonality
        trend = np.linspace(10000, 15000, n_months)
        seasonality = 2000 * np.sin(np.arange(n_months) * 2 * np.pi / 12)
        noise = np.random.normal(0, 500, n_months)
        
        cash_flow = trend + seasonality + noise
        
        # Generate additional features
        data = {
            'date': dates,
            'cash_flow': cash_flow,
            'month': [d.month for d in dates],
            'quarter': [(d.month - 1) // 3 + 1 for d in dates],
        }
        
        df = pd.DataFrame(data)
        
        # Create lagged features
        for lag in [1, 3, 6, 12]:
            if lag < len(df):
                df[f'cash_flow_lag_{lag}'] = df['cash_flow'].shift(lag)
        
        df = df.dropna()
        
        return df
    
    def create_features(self, df: pd.DataFrame, lookback: int = 6) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time series forecasting
        
        Args:
            df: Input dataframe
            lookback: Number of previous timesteps to use as input
            
        Returns:
            X, y arrays
        """
        cash_flows = df['cash_flow'].values
        X, y = [], []
        
        for i in range(len(cash_flows) - lookback):
            X.append(cash_flows[i:i+lookback])
            y.append(cash_flows[i+lookback])
        
        return np.array(X), np.array(y)
    
    def train_forecasting_models(self, df: pd.DataFrame):
        """Train cash flow forecasting models"""
        print("Training cash flow forecasting models...\n")
        
        # Prepare data
        X, y = self.create_features(df, lookback=6)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )
        
        # Scale data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.X_test_original = X_test
        self.y_test = y_test
        
        # Linear Regression
        print("  • Training Linear Regression...")
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        self.models['Linear Regression'] = lr_model
        
        # Polynomial Regression
        print("  • Training Polynomial Regression...")
        poly_features = PolynomialFeatures(degree=2)
        X_train_poly = poly_features.fit_transform(X_train)
        X_test_poly = poly_features.transform(X_test)
        
        poly_model = LinearRegression()
        poly_model.fit(X_train_poly, y_train)
        self.models['Polynomial Regression'] = (poly_model, poly_features)
        
        # Random Forest Regressor
        print("  • Training Random Forest Regressor...")
        rf_model = RandomForestRegressor(n_estimators=100, random_state=self.random_state, n_jobs=-1)
        rf_model.fit(X_train, y_train)
        self.models['Random Forest'] = rf_model
        
        # Gradient Boosting Regressor
        print("  • Training Gradient Boosting Regressor...")
        from sklearn.ensemble import GradientBoostingRegressor
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=self.random_state)
        gb_model.fit(X_train, y_train)
        self.models['Gradient Boosting'] = gb_model
        
        self.X_train = X_train
        self.X_test = X_test
        self.X_test_scaled = X_test_scaled
        self.X_test_poly = X_test_poly
        
        print("✓ Models trained\n")
    
    def evaluate_forecasting_models(self) -> Dict:
        """Evaluate forecasting models"""
        print("Evaluating forecasting models...\n")
        results = {}
        
        for model_name, model in self.models.items():
            print(f"  {model_name}:")
            
            # Get predictions
            if model_name == 'Polynomial Regression':
                poly_model, poly_features = model
                y_pred = poly_model.predict(self.X_test_poly)
            else:
                y_pred = model.predict(self.X_test)
            
            # Calculate metrics
            mae = mean_absolute_error(self.y_test, y_pred)
            mse = mean_squared_error(self.y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(self.y_test, y_pred)
            mape = np.mean(np.abs((self.y_test - y_pred) / self.y_test)) * 100
            
            results[model_name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'mape': mape,
                'y_pred': y_pred
            }
            
            print(f"    MAE: ${mae:.2f}")
            print(f"    RMSE: ${rmse:.2f}")
            print(f"    R² Score: {r2:.4f}")
            print(f"    MAPE: {mape:.2f}%")
            print()
        
        self.results = results
        return results
    
    def plot_predictions(self, figsize: Tuple = (15, 10)):
        """Plot actual vs predicted cash flows"""
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()
        
        for idx, (model_name, metrics) in enumerate(self.results.items()):
            ax = axes[idx]
            
            y_pred = metrics['y_pred']
            
            # Plot actual vs predicted
            ax.plot(self.y_test, 'o-', linewidth=2, markersize=4, 
                   color='#1F77B4', label='Actual')
            ax.plot(y_pred, 's--', linewidth=2, markersize=4, 
                   color='#FF7F0E', label='Predicted', alpha=0.7)
            
            # Add metrics
            r2 = metrics['r2']
            rmse = metrics['rmse']
            
            ax.set_title(f'{model_name} (R²={r2:.4f}, RMSE=${rmse:.0f})', 
                        fontsize=11, fontweight='bold')
            ax.set_xlabel('Sample', fontsize=10)
            ax.set_ylabel('Cash Flow ($)', fontsize=10)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_residuals(self, figsize: Tuple = (15, 10)):
        """Plot residuals analysis"""
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        axes = axes.flatten()
        
        for idx, (model_name, metrics) in enumerate(self.results.items()):
            ax = axes[idx]
            
            residuals = self.y_test - metrics['y_pred']
            
            ax.scatter(metrics['y_pred'], residuals, alpha=0.6, color='#1F77B4')
            ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
            
            ax.set_title(f'{model_name} - Residual Plot', fontsize=11, fontweight='bold')
            ax.set_xlabel('Predicted Value ($)', fontsize=10)
            ax.set_ylabel('Residuals ($)', fontsize=10)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


def main():
    """Main function demonstrating fraud detection and cash flow forecasting"""
    
    print(f"\n{'='*70}")
    print("FINANCIAL MACHINE LEARNING PROJECT")
    print(f"{'='*70}\n")
    
    # ========== FRAUD DETECTION ==========
    print("1. FINANCIAL FRAUD DETECTION")
    print(f"{'-'*70}\n")
    
    try:
        # Initialize and train fraud detection model
        fraud_model = FraudDetectionModel()
        
        # Generate transaction data
        print("Generating synthetic transaction data...")
        df_fraud = fraud_model.generate_transaction_data(n_samples=5000)
        print(f"✓ Generated {len(df_fraud)} transactions")
        print(f"  Fraud cases: {df_fraud['is_fraud'].sum()} ({df_fraud['is_fraud'].sum()/len(df_fraud)*100:.2f}%)\n")
        
        # Preprocess data
        fraud_model.preprocess_data(df_fraud)
        
        # Train models
        fraud_model.train_models()
        
        # Evaluate models
        fraud_results = fraud_model.evaluate_models()
        
        # Display feature importance
        print("Feature Importance Ranking:\n")
        importance = fraud_model.get_feature_importance()
        for model_name, features in importance.items():
            print(f"  {model_name}:")
            sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
            for feature, score in sorted_features[:5]:
                print(f"    • {feature}: {score:.4f}")
            print()
        
        # Generate visualizations
        print("Generating fraud detection visualizations...\n")
        
        fig_roc = fraud_model.plot_roc_curves()
        fig_roc.savefig('/workspaces/reisfitz/fraud_detection_01_roc_curves.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: fraud_detection_01_roc_curves.png")
        
        fig_cm = fraud_model.plot_confusion_matrices()
        fig_cm.savefig('/workspaces/reisfitz/fraud_detection_02_confusion_matrices.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: fraud_detection_02_confusion_matrices.png")
        
        fig_imp = fraud_model.plot_feature_importance()
        fig_imp.savefig('/workspaces/reisfitz/fraud_detection_03_feature_importance.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: fraud_detection_03_feature_importance.png")
        
    except Exception as e:
        print(f"Error in fraud detection: {e}")
    
    print()
    
    # ========== CASH FLOW FORECASTING ==========
    print("2. CASH FLOW FORECASTING")
    print(f"{'-'*70}\n")
    
    try:
        # Initialize cash flow model
        cashflow_model = CashFlowForecastingModel()
        
        # Generate cash flow data
        print("Generating synthetic cash flow data...")
        df_cashflow = cashflow_model.generate_cashflow_data(n_months=48)
        print(f"✓ Generated {len(df_cashflow)} months of data")
        print(f"  Average monthly cash flow: ${df_cashflow['cash_flow'].mean():.2f}\n")
        
        # Train models
        cashflow_model.train_forecasting_models(df_cashflow)
        
        # Evaluate models
        cashflow_results = cashflow_model.evaluate_forecasting_models()
        
        # Generate visualizations
        print("Generating cash flow forecasting visualizations...\n")
        
        fig_pred = cashflow_model.plot_predictions()
        fig_pred.savefig('/workspaces/reisfitz/cashflow_forecasting_01_predictions.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: cashflow_forecasting_01_predictions.png")
        
        fig_resid = cashflow_model.plot_residuals()
        fig_resid.savefig('/workspaces/reisfitz/cashflow_forecasting_02_residuals.png', dpi=100, bbox_inches='tight')
        print("✓ Saved: cashflow_forecasting_02_residuals.png")
        
    except Exception as e:
        print(f"Error in cash flow forecasting: {e}")
    
    print()
    
    # Summary Report
    print(f"{'='*70}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*70}\n")
    
    print("Fraud Detection Best Model:")
    best_fraud_model = max(fraud_results.items(), key=lambda x: x[1]['auc_score'])
    print(f"  Model: {best_fraud_model[0]}")
    print(f"  AUC Score: {best_fraud_model[1]['auc_score']:.4f}")
    print(f"  F1 Score: {best_fraud_model[1]['f1_score']:.4f}")
    print()
    
    print("Cash Flow Forecasting Best Model:")
    best_cf_model = max(cashflow_results.items(), key=lambda x: x[1]['r2'])
    print(f"  Model: {best_cf_model[0]}")
    print(f"  R² Score: {best_cf_model[1]['r2']:.4f}")
    print(f"  RMSE: ${best_cf_model[1]['rmse']:.2f}")
    print()
    
    print(f"{'='*70}")
    print("Project completed successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
