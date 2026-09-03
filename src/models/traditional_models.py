import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                            roc_auc_score, average_precision_score, confusion_matrix,
                            classification_report)
import xgboost as xgb
import joblib
import json
import time
import logging
from typing import Dict, Any, Tuple, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class TraditionalModelTrainer:
    def __init__(self, model_type: str, random_state: int = 42):
        self.model_type = model_type
        self.random_state = random_state
        self.model = None
        self.best_params = {}
        self.training_time = 0
        self.feature_names = []
    
    def get_model(self, params: Dict = None) -> Any:
        """Get model instance with parameters"""
        params = params or {}
        
        if self.model_type == 'RandomForest':
            return RandomForestClassifier(
                n_estimators=params.get('n_estimators', 100),
                max_depth=params.get('max_depth', 10),
                min_samples_split=params.get('min_samples_split', 5),
                min_samples_leaf=params.get('min_samples_leaf', 2),
                max_features=params.get('max_features', 'sqrt'),
                class_weight=params.get('class_weight', 'balanced'),
                random_state=self.random_state,
                n_jobs=-1
            )
        elif self.model_type == 'XGBoost':
            return xgb.XGBClassifier(
                n_estimators=params.get('n_estimators', 100),
                max_depth=params.get('max_depth', 6),
                learning_rate=params.get('learning_rate', 0.1),
                subsample=params.get('subsample', 0.8),
                colsample_bytree=params.get('colsample_bytree', 0.8),
                scale_pos_weight=params.get('scale_pos_weight', 1),
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='logloss'
            )
        elif self.model_type == 'SVM':
            return SVC(
                C=params.get('C', 1.0),
                kernel=params.get('kernel', 'rbf'),
                gamma=params.get('gamma', 'scale'),
                class_weight=params.get('class_weight', 'balanced'),
                probability=True,
                random_state=self.random_state
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def get_param_grid(self) -> Dict:
        """Get hyperparameter grid for tuning"""
        if self.model_type == 'RandomForest':
            return {
                'n_estimators': [100, 200, 300],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2', None],
                'class_weight': ['balanced', 'balanced_subsample']
            }
        elif self.model_type == 'XGBoost':
            return {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9],
                'scale_pos_weight': [1, 5, 10]
            }
        elif self.model_type == 'SVM':
            return {
                'C': [0.1, 1, 10, 100],
                'kernel': ['rbf', 'linear'],
                'gamma': ['scale', 'auto', 0.01, 0.1, 1],
                'class_weight': ['balanced', None]
            }
        return {}
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              tune_hyperparams: bool = False, cv_folds: int = 3) -> Dict:
        """Train the model"""
        start_time = time.time()
        
        if tune_hyperparams:
            logger.info(f"Tuning hyperparameters for {self.model_type}...")
            param_grid = self.get_param_grid()
            
            # Use TimeSeriesSplit for temporal data
            tscv = TimeSeriesSplit(n_splits=cv_folds)
            
            # Use RandomizedSearchCV for efficiency
            search = RandomizedSearchCV(
                self.get_model(),
                param_distributions=param_grid,
                n_iter=20,
                cv=tscv,
                scoring='f1',
                n_jobs=-1,
                random_state=self.random_state,
                verbose=1
            )
            search.fit(X_train, y_train)
            self.model = search.best_estimator_
            self.best_params = search.best_params_
            logger.info(f"Best params: {self.best_params}")
        else:
            self.model = self.get_model()
            self.model.fit(X_train, y_train)
        
        self.training_time = time.time() - start_time
        logger.info(f"{self.model_type} trained in {self.training_time:.2f}s")
        
        # Evaluate on validation set if provided
        metrics = {}
        if X_val is not None and y_val is not None:
            metrics = self.evaluate(X_val, y_val)
        
        return metrics
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model performance"""
        start_time = time.time()
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)[:, 1] if hasattr(self.model, 'predict_proba') else y_pred
        inference_time = time.time() - start_time
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'pr_auc': average_precision_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'inference_time_per_sample': inference_time / len(X),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist(),
            'classification_report': classification_report(y, y_pred, output_dict=True)
        }
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)[:, 1]
        return self.model.predict(X)
    
    def save_model(self, path: str, metadata: Dict = None):
        """Save model and metadata"""
        joblib.dump(self.model, path)
        
        meta = {
            'model_type': self.model_type,
            'best_params': self.best_params,
            'training_time': self.training_time,
            'feature_names': self.feature_names,
            'metadata': metadata or {}
        }
        
        meta_path = path.replace('.joblib', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2, default=str)
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model"""
        self.model = joblib.load(path)
        meta_path = path.replace('.joblib', '_meta.json')
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                self.best_params = meta.get('best_params', {})
                self.training_time = meta.get('training_time', 0)
                self.feature_names = meta.get('feature_names', [])
        except FileNotFoundError:
            pass

def train_all_traditional_models(X_train, y_train, X_val, y_val, tune=False) -> Dict:
    """Train all traditional models and return results"""
    results = {}
    models = {}
    
    for model_type in ['RandomForest', 'XGBoost', 'SVM']:
        logger.info(f"\n{'='*50}")
        logger.info(f"Training {model_type}")
        logger.info(f"{'='*50}")
        
        trainer = TraditionalModelTrainer(model_type)
        metrics = trainer.train(X_train, y_train, X_val, y_val, tune_hyperparams=tune)
        
        # Save model
        model_path = settings.MODELS_DIR / f"{model_type.lower()}_model.joblib"
        trainer.save_model(str(model_path), {'val_metrics': metrics})
        
        results[model_type] = metrics
        models[model_type] = trainer
    
    return results, models

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with dummy data
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=1000, n_features=20, n_informative=10, 
                               n_redundant=5, weights=[0.9, 0.1], random_state=42)
    
    split = int(0.7 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    results, models = train_all_traditional_models(X_train, y_train, X_val, y_val, tune=False)
    
    for model_type, metrics in results.items():
        print(f"\n{model_type}:")
        for k, v in metrics.items():
            if k not in ['confusion_matrix', 'classification_report']:
                print(f"  {k}: {v}")