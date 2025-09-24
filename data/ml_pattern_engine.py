"""
ML Pattern Recognition Engine for SchwaOptions Phase 5
Core AI system for unusual activity detection and pattern matching
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MLPatternEngine:
    """Core ML engine for pattern recognition and anomaly detection"""

    def __init__(self):
        self.unusual_activity_model = None
        self.anomaly_detector = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = []

    def extract_features(self, options_data: pd.DataFrame) -> pd.DataFrame:
        """Extract ML features from options data"""
        features = pd.DataFrame()

        # Volume-based features
        features['volume'] = options_data.get('totalVolume', 0)
        features['avg_volume_ratio'] = features['volume'] / (options_data.get('avg_volume', 1) + 1e-6)
        features['volume_spike'] = (features['volume'] > features['volume'].quantile(0.95)).astype(int)

        # Premium and activity features
        features['premium'] = options_data.get('mark', 0) * options_data.get('totalVolume', 0)
        features['bid_ask_spread'] = options_data.get('ask', 0) - options_data.get('bid', 0)
        features['open_interest'] = options_data.get('openInterest', 0)
        features['oi_volume_ratio'] = features['volume'] / (features['open_interest'] + 1)

        # Greeks-based features
        features['delta'] = options_data.get('delta', 0)
        features['gamma'] = options_data.get('gamma', 0)
        features['theta'] = options_data.get('theta', 0)
        features['vega'] = options_data.get('vega', 0)

        # Volatility features
        features['implied_vol'] = options_data.get('volatility', 0)
        features['iv_rank'] = options_data.get('iv_rank', 50) / 100

        # Time and strike features
        features['days_to_exp'] = options_data.get('daysToExpiration', 30)
        features['moneyness'] = options_data.get('strike', 100) / options_data.get('underlying_price', 100)

        return features

    def train_unusual_activity_detector(self, historical_data: List[Dict]) -> Dict[str, float]:
        """Train ML model on historical unusual activity patterns"""
        try:
            # Prepare training data
            df = pd.DataFrame(historical_data)
            features = self.extract_features(df)

            # Create labels (1 for unusual, 0 for normal)
            labels = self._create_unusual_activity_labels(df)

            # Split and scale data
            X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train Random Forest classifier
            self.unusual_activity_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.unusual_activity_model.fit(X_train_scaled, y_train)

            # Train anomaly detector
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.anomaly_detector.fit(X_train_scaled)

            # Evaluate
            y_pred = self.unusual_activity_model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)

            self.feature_columns = features.columns.tolist()
            self.is_trained = True

            logger.info(f"ML model trained successfully. Accuracy: {accuracy:.3f}")

            return {
                'accuracy': accuracy,
                'feature_importance': dict(zip(self.feature_columns, self.unusual_activity_model.feature_importances_)),
                'n_features': len(self.feature_columns),
                'n_samples': len(historical_data)
            }

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {'error': str(e)}

    def predict_unusual_activity(self, options_data: pd.DataFrame) -> Dict[str, float]:
        """Predict unusual activity probability using trained ML model"""
        if not self.is_trained:
            return {'probability': 0.5, 'confidence': 0.0, 'ml_score': 0.0}

        try:
            features = self.extract_features(options_data)
            features_scaled = self.scaler.transform(features[self.feature_columns])

            # Get probability predictions
            probabilities = self.unusual_activity_model.predict_proba(features_scaled)
            unusual_prob = probabilities[:, 1].mean()

            # Get anomaly score
            anomaly_score = self.anomaly_detector.decision_function(features_scaled).mean()

            # Combine scores for final ML score
            ml_score = (unusual_prob * 0.7 + (1 - anomaly_score) * 0.3)

            return {
                'probability': float(unusual_prob),
                'anomaly_score': float(anomaly_score),
                'ml_score': float(ml_score),
                'confidence': float(abs(unusual_prob - 0.5) * 2)
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {'probability': 0.5, 'confidence': 0.0, 'ml_score': 0.0}

    def _create_unusual_activity_labels(self, df: pd.DataFrame) -> np.ndarray:
        """Create training labels based on unusual activity criteria"""
        # Simple heuristic for labeling (can be enhanced)
        volume_threshold = df['totalVolume'].quantile(0.9)
        premium_threshold = (df.get('mark', 0) * df.get('totalVolume', 0)).quantile(0.9)

        labels = (
            (df.get('totalVolume', 0) > volume_threshold) |
            ((df.get('mark', 0) * df.get('totalVolume', 0)) > premium_threshold)
        ).astype(int)

        return labels.values

    def save_model(self, filepath: str) -> bool:
        """Save trained model to disk"""
        try:
            model_data = {
                'unusual_activity_model': self.unusual_activity_model,
                'anomaly_detector': self.anomaly_detector,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, filepath)
            return True
        except Exception as e:
            logger.error(f"Model save failed: {e}")
            return False

    def load_model(self, filepath: str) -> bool:
        """Load trained model from disk"""
        try:
            model_data = joblib.load(filepath)
            self.unusual_activity_model = model_data['unusual_activity_model']
            self.anomaly_detector = model_data['anomaly_detector']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            return True
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return False

# Global ML engine instance
ml_engine = MLPatternEngine()