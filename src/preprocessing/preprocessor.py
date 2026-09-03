import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from scipy import stats
import joblib
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []
        self.target_name = 'falla'
        self.outlier_bounds = {}
        
    def load_data_from_db(self, equipo_id: int = None, days_back: int = 730) -> pd.DataFrame:
        """Load sensor data from database and pivot to wide format"""
        from src.db.connection import db_pool
        
        query = """
            SELECT 
                l.timestamp,
                e.id as equipo_id,
                e.codigo as equipo_codigo,
                e.tipo as equipo_tipo,
                s.tipo_sensor,
                l.valor,
                l.calidad_dato
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            JOIN equipos e ON e.id = s.equipo_id
            WHERE l.timestamp >= %s
        """
        params = [pd.Timestamp.now() - pd.Timedelta(days=days_back)]
        
        if equipo_id:
            query += " AND e.id = %s"
            params.append(equipo_id)
        
        query += " ORDER BY e.id, l.timestamp"
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame()
        
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Pivot to wide format
        df_pivot = df.pivot_table(
            index=['timestamp', 'equipo_id', 'equipo_codigo', 'equipo_tipo'],
            columns='tipo_sensor',
            values='valor',
            aggfunc='mean'
        ).reset_index()
        
        df_pivot.columns.name = None
        return df_pivot
    
    def create_target_variable(self, df: pd.DataFrame, prediction_window_hours: int = 12) -> pd.DataFrame:
        """Create target variable: failure in next N hours based on threshold breaches"""
        df = df.copy()
        df = df.sort_values(['equipo_id', 'timestamp'])
        df[self.target_name] = 0
        
        for equipo_id in df['equipo_id'].unique():
            mask = df['equipo_id'] == equipo_id
            eq_idx = df[mask].index
            
            vib_val = df.loc[eq_idx, 'vibracion'] if 'vibracion' in df.columns else pd.Series(0, index=eq_idx)
            temp_val = df.loc[eq_idx, 'temperatura'] if 'temperatura' in df.columns else pd.Series(0, index=eq_idx)
            
            is_anomaly = (
                (vib_val > vib_val.quantile(0.97)) |
                (temp_val > temp_val.quantile(0.97))
            )
            shifted = is_anomaly.shift(-prediction_window_hours).fillna(False)
            df.loc[eq_idx, self.target_name] = shifted.astype(int)
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'median') -> pd.DataFrame:
        """Handle missing values"""
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if df[col].isnull().any():
                if col not in self.imputers:
                    self.imputers[col] = SimpleImputer(strategy=strategy)
                    df[col] = self.imputers[col].fit_transform(df[[col]]).flatten()
                else:
                    df[col] = self.imputers[col].transform(df[[col]]).flatten()
        
        df = df.fillna(0)
        return df
    
    def remove_duplicates(self, df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
        """Remove duplicate rows"""
        df = df.copy()
        initial_len = len(df)
        df = df.drop_duplicates(subset=subset or ['timestamp', 'equipo_id'])
        removed = initial_len - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate rows")
        return df
    
    def detect_outliers_iqr(self, df: pd.DataFrame, columns: List[str] = None, factor: float = 1.5) -> Dict:
        """Detect outliers using IQR method"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        bounds = {}
        for col in columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - factor * IQR
            upper = Q3 + factor * IQR
            bounds[col] = (lower, upper)
            self.outlier_bounds[col] = (lower, upper)
        
        return bounds
    
    def cap_outliers(self, df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """Cap outliers using precomputed bounds"""
        df = df.copy()
        if columns is None:
            columns = self.outlier_bounds.keys()
        
        for col in columns:
            if col in self.outlier_bounds:
                lower, upper = self.outlier_bounds[col]
                df[col] = df[col].clip(lower, upper)
        
        return df
    
    def detect_outliers_zscore(self, df: pd.DataFrame, columns: List[str] = None, threshold: float = 3) -> pd.DataFrame:
        """Detect outliers using Z-score"""
        df = df.copy()
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        outlier_mask = pd.Series(False, index=df.index)
        for col in columns:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            outlier_mask |= (z_scores > threshold)
        
        return df[~outlier_mask]
    
    def fit_scalers(self, df: pd.DataFrame, method: str = 'standard', columns: List[str] = None):
        """Fit scalers on training data"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
            columns = [c for c in columns if c not in [self.target_name, 'equipo_id']]
        
        if method == 'standard':
            scaler_class = StandardScaler
        elif method == 'minmax':
            scaler_class = MinMaxScaler
        else:
            raise ValueError(f"Unknown scaling method: {method}")
        
        for col in columns:
            if col in df.columns:
                self.scalers[col] = scaler_class()
                self.scalers[col].fit(df[[col]].dropna())
    
    def transform_scalers(self, df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """Transform data using fitted scalers"""
        df = df.copy()
        if columns is None:
            columns = self.scalers.keys()
        
        for col in columns:
            if col in df.columns and col in self.scalers:
                df[col] = self.scalers[col].transform(df[[col]])
        
        return df
    
    def fit_encoders(self, df: pd.DataFrame, columns: List[str] = None):
        """Fit encoders for categorical columns"""
        if columns is None:
            columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in columns:
            if col in df.columns:
                self.encoders[col] = LabelEncoder()
                self.encoders[col].fit(df[col].dropna())
    
    def transform_encoders(self, df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """Transform categorical columns using fitted encoders"""
        df = df.copy()
        if columns is None:
            columns = self.encoders.keys()
        
        for col in columns:
            if col in df.columns and col in self.encoders:
                # Handle unseen labels
                mask = df[col].isin(self.encoders[col].classes_)
                df.loc[mask, col] = self.encoders[col].transform(df.loc[mask, col])
                df.loc[~mask, col] = -1  # Unknown category
        
        return df
    
    def create_features(self, df: pd.DataFrame, window_sizes: List[int] = [6, 12, 24, 48]) -> pd.DataFrame:
        """Create time-series features"""
        df = df.copy()
        df = df.sort_values(['equipo_id', 'timestamp'])
        
        sensor_cols = [c for c in df.columns if c in settings.SENSOR_TYPES]
        
        for equipo_id in df['equipo_id'].unique():
            mask = df['equipo_id'] == equipo_id
            equipo_data = df[mask].copy()
            
            for col in sensor_cols:
                if col not in equipo_data.columns:
                    continue
                
                # Rolling statistics
                for window in window_sizes:
                    df.loc[mask, f'{col}_mean_{window}h'] = (
                        equipo_data[col].rolling(window=window, min_periods=1).mean().values
                    )
                    df.loc[mask, f'{col}_std_{window}h'] = (
                        equipo_data[col].rolling(window=window, min_periods=1).std().fillna(0).values
                    )
                    df.loc[mask, f'{col}_min_{window}h'] = (
                        equipo_data[col].rolling(window=window, min_periods=1).min().values
                    )
                    df.loc[mask, f'{col}_max_{window}h'] = (
                        equipo_data[col].rolling(window=window, min_periods=1).max().values
                    )
                
                # Degradation indicators
                df.loc[mask, f'{col}_trend_24h'] = (
                    equipo_data[col].rolling(window=24, min_periods=2).apply(
                        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
                    ).fillna(0).values
                )
                
                # Ratio features
                if col == 'temperatura' and 'presion_aceite' in equipo_data.columns:
                    df.loc[mask, 'temp_presion_ratio'] = (
                        equipo_data['temperatura'] / equipo_data['presion_aceite'].replace(0, np.nan)
                    ).fillna(0).values
                
                if col == 'vibracion' and 'rpm' in equipo_data.columns:
                    df.loc[mask, 'vib_rpm_ratio'] = (
                        equipo_data['vibracion'] / equipo_data['rpm'].replace(0, np.nan)
                    ).fillna(0).values
            
            # Time since last maintenance (using quality alerts as proxy)
            if 'calidad_dato' in equipo_data.columns:
                # Not in pivoted format, skip
                pass
        
        return df
    
    def prepare_sequences(self, df: pd.DataFrame, sequence_length: int = 24, 
                          target_col: str = 'falla') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM/CNN models"""
        sensor_cols = [c for c in df.columns if c in settings.SENSOR_TYPES or 
                       any(c.startswith(s + '_') for s in settings.SENSOR_TYPES)]
        sensor_cols = [c for c in sensor_cols if c != target_col]
        
        X, y = [], []
        for equipo_id in df['equipo_id'].unique():
            equipo_data = df[df['equipo_id'] == equipo_id].sort_values('timestamp')
            values = equipo_data[sensor_cols].values
            targets = equipo_data[target_col].values
            
            for i in range(len(values) - sequence_length):
                X.append(values[i:i+sequence_length])
                y.append(targets[i+sequence_length])
        
        return np.array(X), np.array(y)
    
    def temporal_split(self, df: pd.DataFrame, train_ratio: float = 0.7, 
                       val_ratio: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split data temporally to avoid leakage"""
        df = df.sort_values('timestamp').reset_index(drop=True)
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()
        
        logger.info(f"Temporal split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        return train_df, val_df, test_df
    
    def save_transformers(self, path: str):
        """Save fitted transformers"""
        transformers = {
            'scalers': self.scalers,
            'encoders': self.encoders,
            'imputers': self.imputers,
            'outlier_bounds': self.outlier_bounds,
            'feature_names': self.feature_names
        }
        joblib.dump(transformers, path)
        logger.info(f"Transformers saved to {path}")
    
    def load_transformers(self, path: str):
        """Load fitted transformers"""
        transformers = joblib.load(path)
        self.scalers = transformers.get('scalers', {})
        self.encoders = transformers.get('encoders', {})
        self.imputers = transformers.get('imputers', {})
        self.outlier_bounds = transformers.get('outlier_bounds', {})
        self.feature_names = transformers.get('feature_names', [])
        logger.info(f"Transformers loaded from {path}")

def prepare_training_data(equipo_id: int = None, days_back: int = 730) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Complete preprocessing pipeline"""
    preprocessor = DataPreprocessor()
    
    # Load data
    logger.info("Loading data from database...")
    df = preprocessor.load_data_from_db(equipo_id, days_back)
    
    if df.empty:
        raise ValueError("No data found")
    
    # Create target
    df = preprocessor.create_target_variable(df)
    
    # Handle missing values
    df = preprocessor.handle_missing_values(df)
    
    # Remove duplicates
    df = preprocessor.remove_duplicates(df)
    
    # Detect and cap outliers
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ['equipo_id', 'falla']]
    preprocessor.detect_outliers_iqr(df, numeric_cols)
    df = preprocessor.cap_outliers(df, numeric_cols)
    
    # Create features
    df = preprocessor.create_features(df)
    
    # Handle new missing values from feature creation
    df = preprocessor.handle_missing_values(df)
    
    # Encode categorical
    cat_cols = ['equipo_tipo']
    preprocessor.fit_encoders(df, cat_cols)
    df = preprocessor.transform_encoders(df, cat_cols)
    
    # Scale numeric
    num_cols = [c for c in df.select_dtypes(include=[np.number]).columns 
                if c not in ['equipo_id', 'falla']]
    preprocessor.fit_scalers(df, 'standard', num_cols)
    df = preprocessor.transform_scalers(df, num_cols)
    
    # Temporal split
    train_df, val_df, test_df = preprocessor.temporal_split(df)
    
    # Save transformers
    preprocessor.save_transformers(settings.MODELS_DIR / "preprocessors.joblib")
    
    return train_df, val_df, test_df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_pool.initialize()
    train, val, test = prepare_training_data()
    print(f"Train: {train.shape}, Val: {val.shape}, Test: {test.shape}")
    print(f"Features: {train.shape[1]}")
    print(f"Target distribution - Train: {train['falla'].mean():.2%}, Val: {val['falla'].mean():.2%}, Test: {test['falla'].mean():.2%}")