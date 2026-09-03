import numpy as np

from src.evaluation.evaluator import ModelEvaluator
from src.models.traditional_models import TraditionalModelTrainer


def test_metrics_and_cross_validation_are_numeric():
    X = np.random.rand(60, 5)
    y = np.random.randint(0, 2, size=60)

    rf = TraditionalModelTrainer('RandomForest')
    rf.train(X[:45], y[:45], X[45:], y[45:])

    evaluator = ModelEvaluator({'rf': rf}, X[45:], y[45:])
    results = evaluator.evaluate_all()
    for metric_name in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']:
        assert isinstance(results['rf'][metric_name], float)

    cv = evaluator.cross_validate(X, y, cv_method='stratified', n_splits=3)
    assert 'rf' in cv
    assert set(cv['rf'].keys()) >= {'accuracy', 'precision', 'recall', 'f1', 'roc_auc'}
