import numpy as np
from sklearn.datasets import make_classification

from src.models.traditional_models import TraditionalModelTrainer


def test_random_forest_and_xgboost_train():
    X, y = make_classification(
        n_samples=200,
        n_features=12,
        n_informative=8,
        n_redundant=2,
        n_classes=2,
        weights=[0.75, 0.25],
        random_state=42,
    )

    rf = TraditionalModelTrainer('RandomForest')
    rf.train(X[:150], y[:150], X[150:], y[150:])
    assert rf.model is not None

    xgb = TraditionalModelTrainer('XGBoost')
    xgb.train(X[:150], y[:150], X[150:], y[150:])
    assert xgb.model is not None
