import numpy as np
import pandas as pd

from src.preprocessing.preprocessor import DataPreprocessor


def test_missing_values_and_scaling():
    df = pd.DataFrame({
        'equipo_id': [1, 1, 2, 2],
        'timestamp': pd.date_range('2024-01-01', periods=4, freq='H'),
        'temperatura': [80.0, np.nan, 82.0, 83.0],
        'vibracion': [2.0, 2.5, np.nan, 3.0],
        'falla': [0, 1, 0, 1],
    })

    prep = DataPreprocessor()
    cleaned = prep.handle_missing_values(df)
    assert cleaned['temperatura'].isna().sum() == 0
    assert cleaned['vibracion'].isna().sum() == 0

    prep.fit_scalers(cleaned, columns=['temperatura', 'vibracion'])
    scaled = prep.transform_scalers(cleaned, columns=['temperatura', 'vibracion'])
    assert scaled['temperatura'].notna().all()
    assert scaled['vibracion'].notna().all()
