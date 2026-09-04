import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import ttest_rel, chi2_contingency
from sklearn.model_selection import TimeSeriesSplit, StratifiedKFold, cross_val_score
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                            roc_auc_score, average_precision_score, confusion_matrix)
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class ModelEvaluator:
    def __init__(self, models: Dict, X_test: np.ndarray, y_test: np.ndarray):
        self.models = models
        self.X_test = X_test
        self.y_test = y_test
        self.results = {}
    
    def evaluate_all(self) -> Dict:
        """Evaluate all models on test set"""
        for name, model in self.models.items():
            logger.info(f"Evaluating {name}...")
            
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(self.X_test)
                y_pred = model.predict(self.X_test)
            else:
                y_proba = model.predict(self.X_test)
                y_pred = (y_proba > 0.5).astype(int)
            
            self.results[name] = {
                'accuracy': accuracy_score(self.y_test, y_pred),
                'precision': precision_score(self.y_test, y_pred, zero_division=0),
                'recall': recall_score(self.y_test, y_pred, zero_division=0),
                'f1_score': f1_score(self.y_test, y_pred, zero_division=0),
                'roc_auc': roc_auc_score(self.y_test, y_proba) if len(np.unique(self.y_test)) > 1 else 0,
                'pr_auc': average_precision_score(self.y_test, y_proba) if len(np.unique(self.y_test)) > 1 else 0,
                'confusion_matrix': confusion_matrix(self.y_test, y_pred).tolist()
            }
            
            logger.info(f"  Accuracy: {self.results[name]['accuracy']:.4f}")
            logger.info(f"  F1-Score: {self.results[name]['f1_score']:.4f}")
            logger.info(f"  ROC-AUC: {self.results[name]['roc_auc']:.4f}")
        
        return self.results
    
    def cross_validate(self, X: np.ndarray, y: np.ndarray, 
                       cv_method: str = 'timeseries', n_splits: int = 5) -> Dict:
        """Perform cross-validation"""
        cv_results = {}
        
        if cv_method == 'timeseries':
            cv = TimeSeriesSplit(n_splits=n_splits)
        elif cv_method == 'stratified':
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        else:
            cv = n_splits
        
        for name, model in self.models.items():
            logger.info(f"Cross-validating {name} with {cv_method}...")
            
            # Get estimator for sklearn API
            if hasattr(model, 'model'):
                estimator = model.model
            else:
                estimator = model
            
            scores = {}
            for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
                try:
                    cv_scores = cross_val_score(estimator, X, y, cv=cv, 
                                               scoring=metric, n_jobs=-1)
                    scores[metric] = {
                        'mean': cv_scores.mean(),
                        'std': cv_scores.std(),
                        'scores': cv_scores.tolist()
                    }
                except Exception as e:
                    logger.warning(f"CV failed for {name} - {metric}: {e}")
                    scores[metric] = {'mean': 0, 'std': 0, 'scores': []}
            
            cv_results[name] = scores
        
        return cv_results
    
    def paired_t_test(self, model1_name: str, model2_name: str, 
                      metric: str = 'f1_score') -> Dict:
        """Paired t-test between two models"""
        # Need CV scores for each fold
        cv = TimeSeriesSplit(n_splits=5)
        
        model1 = self.models[model1_name]
        model2 = self.models[model2_name]
        
        est1 = model1.model if hasattr(model1, 'model') else model1
        est2 = model2.model if hasattr(model2, 'model') else model2
        
        scores1 = []
        scores2 = []
        
        for train_idx, test_idx in cv.split(self.X_test):
            X_tr, X_te = self.X_test[train_idx], self.X_test[test_idx]
            y_tr, y_te = self.y_test[train_idx], self.y_test[test_idx]
            
            est1.fit(X_tr, y_tr)
            est2.fit(X_tr, y_tr)
            
            if hasattr(est1, 'predict_proba'):
                proba1 = est1.predict_proba(X_te)[:, 1]
                proba2 = est2.predict_proba(X_te)[:, 1]
                pred1 = (proba1 > 0.5).astype(int)
                pred2 = (proba2 > 0.5).astype(int)
            else:
                pred1 = est1.predict(X_te)
                pred2 = est2.predict(X_te)
            
            if metric == 'f1_score':
                scores1.append(f1_score(y_te, pred1, zero_division=0))
                scores2.append(f1_score(y_te, pred2, zero_division=0))
            elif metric == 'accuracy':
                scores1.append(accuracy_score(y_te, pred1))
                scores2.append(accuracy_score(y_te, pred2))
            elif metric == 'roc_auc':
                scores1.append(roc_auc_score(y_te, proba1) if len(np.unique(y_te)) > 1 else 0)
                scores2.append(roc_auc_score(y_te, proba2) if len(np.unique(y_te)) > 1 else 0)
        
        t_stat, p_value = ttest_rel(scores1, scores2)
        
        return {
            'model1': model1_name,
            'model2': model2_name,
            'metric': metric,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'mean_diff': np.mean(scores1) - np.mean(scores2),
            'scores1': scores1,
            'scores2': scores2
        }
    
    def mcnemar_test(self, model1_name: str, model2_name: str) -> Dict:
        """McNemar's test for comparing two classifiers"""
        model1 = self.models[model1_name]
        model2 = self.models[model2_name]
        
        est1 = model1.model if hasattr(model1, 'model') else model1
        est2 = model2.model if hasattr(model2, 'model') else model2
        
        pred1 = est1.predict(self.X_test)
        pred2 = est2.predict(self.X_test)
        
        # Create contingency table
        # n00: both correct, n01: model1 correct, model2 wrong
        # n10: model1 wrong, model2 correct, n11: both wrong
        correct1 = (pred1 == self.y_test)
        correct2 = (pred2 == self.y_test)
        
        n00 = np.sum(correct1 & correct2)
        n01 = np.sum(correct1 & ~correct2)
        n10 = np.sum(~correct1 & correct2)
        n11 = np.sum(~correct1 & ~correct2)
        
        # McNemar's test statistic: (|n01 - n10| - 1)^2 / (n01 + n10)
        if n01 + n10 > 0:
            chi2 = (abs(n01 - n10) - 1) ** 2 / (n01 + n10)
            p_value = 1 - stats.chi2.cdf(chi2, df=1)
        else:
            chi2 = 0
            p_value = 1.0
        
        return {
            'model1': model1_name,
            'model2': model2_name,
            'n00': int(n00),
            'n01': int(n01),
            'n10': int(n10),
            'n11': int(n11),
            'chi2_statistic': chi2,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
    
    def bootstrap_confidence_intervals(self, n_bootstrap: int = 1000, 
                                        confidence: float = 0.95) -> Dict:
        """Bootstrap confidence intervals for metrics"""
        n_samples = len(self.y_test)
        metrics_list = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
        bootstrap_results = {}
        
        for name, model in self.models.items():
            logger.info(f"Bootstrapping {name}...")
            
            est = model.model if hasattr(model, 'model') else model
            
            boot_metrics = {m: [] for m in metrics_list}
            
            for i in range(n_bootstrap):
                # Bootstrap sample
                indices = np.random.choice(n_samples, n_samples, replace=True)
                X_boot = self.X_test[indices]
                y_boot = self.y_test[indices]
                
                if hasattr(est, 'predict_proba'):
                    y_proba = est.predict_proba(X_boot)[:, 1]
                    y_pred = (y_proba > 0.5).astype(int)
                else:
                    y_pred = est.predict(X_boot)
                    y_proba = y_pred
                
                boot_metrics['accuracy'].append(accuracy_score(y_boot, y_pred))
                boot_metrics['precision'].append(precision_score(y_boot, y_pred, zero_division=0))
                boot_metrics['recall'].append(recall_score(y_boot, y_pred, zero_division=0))
                boot_metrics['f1_score'].append(f1_score(y_boot, y_pred, zero_division=0))
                
                if len(np.unique(y_boot)) > 1:
                    boot_metrics['roc_auc'].append(roc_auc_score(y_boot, y_proba))
                else:
                    boot_metrics['roc_auc'].append(0)
            
            # Calculate confidence intervals
            alpha = (1 - confidence) / 2
            ci_results = {}
            for metric, values in boot_metrics.items():
                ci_results[metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'ci_lower': np.percentile(values, alpha * 100),
                    'ci_upper': np.percentile(values, (1 - alpha) * 100)
                }
            
            bootstrap_results[name] = ci_results
        
        return bootstrap_results
    
    def noise_sensitivity(self, noise_levels: List[float] = [0.01, 0.05, 0.1, 0.2]) -> Dict:
        """Test model sensitivity to input noise"""
        sensitivity_results = {}
        
        for name, model in self.models.items():
            logger.info(f"Testing noise sensitivity for {name}...")
            
            est = model.model if hasattr(model, 'model') else model
            base_proba = est.predict_proba(self.X_test)[:, 1] if hasattr(est, 'predict_proba') else est.predict(self.X_test)
            base_pred = (base_proba > 0.5).astype(int)
            base_f1 = f1_score(self.y_test, base_pred, zero_division=0)
            
            noise_results = {}
            for noise_level in noise_levels:
                # Add Gaussian noise
                noise = np.random.normal(0, noise_level, self.X_test.shape)
                X_noisy = self.X_test + noise
                
                if hasattr(est, 'predict_proba'):
                    y_proba = est.predict_proba(X_noisy)[:, 1]
                    y_pred = (y_proba > 0.5).astype(int)
                else:
                    y_pred = est.predict(X_noisy)
                
                f1 = f1_score(self.y_test, y_pred, zero_division=0)
                degradation = (base_f1 - f1) / base_f1 if base_f1 > 0 else 0
                
                noise_results[noise_level] = {
                    'f1_score': f1,
                    'degradation': degradation
                }
            
            sensitivity_results[name] = noise_results
        
        return sensitivity_results
    
    def get_comparison_table(self) -> pd.DataFrame:
        """Get comparison table as DataFrame"""
        if not self.results:
            self.evaluate_all()
        
        rows = []
        for name, metrics in self.results.items():
            row = {'Model': name}
            for k, v in metrics.items():
                if k != 'confusion_matrix':
                    row[k] = v
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df.sort_values('f1_score', ascending=False)
    
    def save_results(self, path: str):
        """Save evaluation results"""
        with open(path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Results saved to {path}")

def compare_all_models(models: Dict, X_test: np.ndarray, y_test: np.ndarray,
                       X_train: np.ndarray = None, y_train: np.ndarray = None) -> Dict:
    """Complete model comparison with statistical tests"""
    evaluator = ModelEvaluator(models, X_test, y_test)
    
    # Test set evaluation
    test_results = evaluator.evaluate_all()
    
    # Cross-validation
    if X_train is not None:
        cv_ts = evaluator.cross_validate(X_train, y_train, 'timeseries')
        cv_strat = evaluator.cross_validate(X_train, y_train, 'stratified')
    else:
        cv_ts = evaluator.cross_validate(X_test, y_test, 'timeseries')
        cv_strat = evaluator.cross_validate(X_test, y_test, 'stratified')
    
    # Statistical tests
    model_names = list(models.keys())
    t_tests = []
    mcnemar_tests = []
    
    for i in range(len(model_names)):
        for j in range(i+1, len(model_names)):
            for metric in ['f1_score', 'accuracy', 'roc_auc']:
                t_test = evaluator.paired_t_test(model_names[i], model_names[j], metric)
                t_tests.append(t_test)
            
            mcnemar = evaluator.mcnemar_test(model_names[i], model_names[j])
            mcnemar_tests.append(mcnemar)
    
    # Bootstrap CIs
    bootstrap_cis = evaluator.bootstrap_confidence_intervals()
    
    # Noise sensitivity
    noise_sensitivity = evaluator.noise_sensitivity()
    
    # Comparison table
    comparison_df = evaluator.get_comparison_table()
    
    full_results = {
        'test_metrics': test_results,
        'cross_validation_timeseries': cv_ts,
        'cross_validation_stratified': cv_strat,
        'paired_t_tests': t_tests,
        'mcnemar_tests': mcnemar_tests,
        'bootstrap_cis': bootstrap_cis,
        'noise_sensitivity': noise_sensitivity,
        'comparison_table': comparison_df.to_dict('records'),
        'best_model': best_model
    }
    
    return full_results


def calculate_weighted_score(comparison_list: List[Dict[str, Any]], weights: Dict[str, float]) -> pd.DataFrame:
    """
    Calculate weighted decision score for model selection based on user-defined criteria weights.
    Weights keys: 'f1_score', 'recall', 'speed', 'interpretability', 'robustness'
    """
    df = pd.DataFrame(comparison_list).copy()

    # Pre-set subjective/technical ratings if not present
    interpretability_map = {
        'Random Forest': 0.85,
        'Support Vector Machine (SVM)': 0.70,
        'SVM': 0.70,
        'XGBoost (Optimizado)': 0.80,
        'XGBoost': 0.80,
        'CNN-LSTM (Deep Learning)': 0.40,
        'CNN-LSTM': 0.40,
        'LSTM-Autoencoder+RF': 0.50
    }
    
    if 'interpretability' not in df.columns:
        df['interpretability'] = df['Model'].map(lambda m: interpretability_map.get(m, 0.70))

    if 'inference_time_ms' in df.columns:
        max_time = df['inference_time_ms'].max() or 1.0
        df['speed_score'] = 1.0 - (df['inference_time_ms'] / (max_time * 1.2))
    else:
        df['speed_score'] = 0.85

    if 'robustness' not in df.columns:
        df['robustness'] = df['f1_score'] * 0.95

    # Normalize weights to sum to 1.0
    w_sum = sum(weights.values()) or 1.0
    norm_w = {k: v / w_sum for k, v in weights.items()}

    # Calculate weighted score (0 to 100%)
    df['weighted_score'] = (
        df['f1_score'] * norm_w.get('f1_score', 0.35) +
        df['recall'] * norm_w.get('recall', 0.25) +
        df['speed_score'] * norm_w.get('speed', 0.15) +
        df['interpretability'] * norm_w.get('interpretability', 0.15) +
        df['robustness'] * norm_w.get('robustness', 0.10)
    ) * 100.0

    df['weighted_score'] = df['weighted_score'].round(2)
    return df.sort_values('weighted_score', ascending=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with dummy data
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.datasets import make_classification
    
    X, y = make_classification(n_samples=500, n_features=20, n_informative=10, 
                               weights=[0.9, 0.1], random_state=42)
    
    split = int(0.7 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    svm = SVC(probability=True, random_state=42)
    
    rf.fit(X_train, y_train)
    svm.fit(X_train, y_train)
    
    models = {'RandomForest': rf, 'SVM': svm}
    
    results = compare_all_models(models, X_test, y_test, X_train, y_train)
    
    print("\nComparison Table:")
    print(pd.DataFrame(results['comparison_table']))
    print(f"\nBest model: {results['best_model']}")