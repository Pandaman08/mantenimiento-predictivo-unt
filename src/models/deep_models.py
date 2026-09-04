import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional

try:
    import tensorflow as tf
    from tensorflow.keras.models import Model, Sequential
    from tensorflow.keras.layers import (Input, Conv1D, LSTM, Dense, Dropout, BatchNormalization,
                                          MaxPooling1D, Flatten, Concatenate, RepeatVector, TimeDistributed)
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from tensorflow.keras.utils import to_categorical
    HAS_TENSORFLOW = True
except (ImportError, ModuleNotFoundError):
    HAS_TENSORFLOW = False
    tf = None
    Model = Any
    Sequential = Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                            roc_auc_score, average_precision_score, confusion_matrix)
import joblib
import json
import time
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

# Set random seeds for reproducibility
if HAS_TENSORFLOW and tf is not None:
    tf.random.set_seed(42)
np.random.seed(42)

class CNNLSTMModel:
    def __init__(self, sequence_length: int = 24, n_features: int = 10, 
                 n_filters: int = 64, lstm_units: int = 64, dropout_rate: float = 0.3,
                 learning_rate: float = 0.001):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.n_filters = n_filters
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.history = None
        self.training_time = 0
    
    def build_model(self) -> Model:
        """Build CNN-LSTM architecture"""
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # CNN layers for local pattern extraction
        x = Conv1D(filters=self.n_filters, kernel_size=3, activation='relu', padding='same')(inputs)
        x = BatchNormalization()(x)
        x = Conv1D(filters=self.n_filters, kernel_size=3, activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.dropout_rate)(x)
        
        x = Conv1D(filters=self.n_filters * 2, kernel_size=3, activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = MaxPooling1D(pool_size=2)(x)
        x = Dropout(self.dropout_rate)(x)
        
        # LSTM layers for temporal dependencies
        x = LSTM(self.lstm_units, return_sequences=True)(x)
        x = Dropout(self.dropout_rate)(x)
        x = LSTM(self.lstm_units // 2, return_sequences=False)(x)
        x = Dropout(self.dropout_rate)(x)
        
        # Dense layers for classification
        x = Dense(64, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(self.dropout_rate)(x)
        x = Dense(32, activation='relu')(x)
        x = Dropout(self.dropout_rate)(x)
        outputs = Dense(1, activation='sigmoid')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc'), 
                     tf.keras.metrics.Precision(name='precision'),
                     tf.keras.metrics.Recall(name='recall')]
        )
        
        self.model = model
        return model
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 50, batch_size: int = 32, class_weight: Dict = None) -> Dict:
        """Train the CNN-LSTM model"""
        if self.model is None:
            self.build_model()
        
        callbacks = [
            EarlyStopping(monitor='val_loss' if X_val is not None else 'loss', 
                         patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss' if X_val is not None else 'loss',
                             factor=0.5, patience=5, min_lr=1e-6),
            ModelCheckpoint(
                filepath=str(settings.MODELS_DIR / 'cnn_lstm_best.h5'),
                monitor='val_loss' if X_val is not None else 'loss',
                save_best_only=True, save_weights_only=True
            )
        ]
        
        val_data = (X_val, y_val) if X_val is not None else None
        
        start_time = time.time()
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=val_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            class_weight=class_weight,
            verbose=1
        )
        self.training_time = time.time() - start_time
        
        logger.info(f"CNN-LSTM trained in {self.training_time:.2f}s")
        
        metrics = {}
        if X_val is not None:
            metrics = self.evaluate(X_val, y_val)
        
        return metrics
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model"""
        start_time = time.time()
        y_proba = self.model.predict(X, verbose=0).flatten()
        y_pred = (y_proba > 0.5).astype(int)
        inference_time = time.time() - start_time
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'pr_auc': average_precision_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'inference_time_per_sample': inference_time / len(X),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        proba = self.model.predict(X, verbose=0).flatten()
        return (proba > 0.5).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        return self.model.predict(X, verbose=0).flatten()
    
    def save_model(self, path: str):
        """Save model"""
        self.model.save(path)
        meta = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'n_filters': self.n_filters,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'training_time': self.training_time
        }
        meta_path = path.replace('.h5', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        logger.info(f"CNN-LSTM model saved to {path}")
    
    def load_model(self, path: str):
        """Load model"""
        self.model = tf.keras.models.load_model(path)
        meta_path = path.replace('.h5', '_meta.json')
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                self.sequence_length = meta.get('sequence_length', 24)
                self.n_features = meta.get('n_features', 10)
                self.n_filters = meta.get('n_filters', 64)
                self.lstm_units = meta.get('lstm_units', 64)
                self.dropout_rate = meta.get('dropout_rate', 0.3)
                self.learning_rate = meta.get('learning_rate', 0.001)
                self.training_time = meta.get('training_time', 0)
        except FileNotFoundError:
            pass


class LSTMAutoencoderRF:
    def __init__(self, sequence_length: int = 24, n_features: int = 10,
                 encoding_dim: int = 32, lstm_units: int = 64, 
                 rf_n_estimators: int = 100, dropout_rate: float = 0.2,
                 learning_rate: float = 0.001):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.encoding_dim = encoding_dim
        self.lstm_units = lstm_units
        self.rf_n_estimators = rf_n_estimators
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.autoencoder = None
        self.encoder = None
        self.rf_model = None
        self.training_time = 0
    
    def build_autoencoder(self) -> Tuple[Model, Model]:
        """Build LSTM Autoencoder"""
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # Encoder
        encoded = LSTM(self.lstm_units, return_sequences=True, activation='tanh')(inputs)
        encoded = Dropout(self.dropout_rate)(encoded)
        encoded = LSTM(self.lstm_units // 2, return_sequences=False, activation='tanh')(encoded)
        encoded = Dropout(self.dropout_rate)(encoded)
        encoded = Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = RepeatVector(self.sequence_length)(encoded)
        decoded = LSTM(self.lstm_units // 2, return_sequences=True, activation='tanh')(decoded)
        decoded = Dropout(self.dropout_rate)(decoded)
        decoded = LSTM(self.lstm_units, return_sequences=True, activation='tanh')(decoded)
        decoded = Dropout(self.dropout_rate)(decoded)
        decoded = TimeDistributed(Dense(self.n_features))(decoded)
        
        # Full autoencoder
        autoencoder = Model(inputs, decoded)
        autoencoder.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='mse')
        
        # Encoder only
        encoder = Model(inputs, encoded)
        
        self.autoencoder = autoencoder
        self.encoder = encoder
        return autoencoder, encoder
    
    def train_autoencoder(self, X_train: np.ndarray, X_val: np.ndarray = None,
                          epochs: int = 50, batch_size: int = 32) -> Dict:
        """Train autoencoder for dimensionality reduction"""
        if self.autoencoder is None:
            self.build_autoencoder()
        
        callbacks = [
            EarlyStopping(monitor='val_loss' if X_val is not None else 'loss',
                         patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss' if X_val is not None else 'loss',
                             factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        val_data = (X_val, X_val) if X_val is not None else None
        
        start_time = time.time()
        history = self.autoencoder.fit(
            X_train, X_train,
            validation_data=val_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Train Random Forest on encoded features
        logger.info("Training Random Forest on encoded features...")
        X_train_encoded = self.encoder.predict(X_train, verbose=0)
        
        self.rf_model = RandomForestClassifier(
            n_estimators=self.rf_n_estimators,
            max_depth=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        # We need labels for RF training - this will be done in train_full
        self.training_time = time.time() - start_time
        
        return {'autoencoder_loss': history.history['loss'][-1]}
    
    def train_full(self, X_train: np.ndarray, y_train: np.ndarray,
                   X_val: np.ndarray = None, y_val: np.ndarray = None,
                   epochs: int = 50, batch_size: int = 32) -> Dict:
        """Train full pipeline: autoencoder + RF"""
        # Train autoencoder
        ae_metrics = self.train_autoencoder(X_train, X_val, epochs, batch_size)
        
        # Encode features
        X_train_encoded = self.encoder.predict(X_train, verbose=0)
        
        # Train RF
        rf_start = time.time()
        self.rf_model.fit(X_train_encoded, y_train)
        rf_time = time.time() - rf_start
        
        self.training_time += rf_time
        
        metrics = {}
        if X_val is not None:
            metrics = self.evaluate(X_val, y_val)
        
        return {**ae_metrics, **metrics}
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Evaluate model"""
        start_time = time.time()
        X_encoded = self.encoder.predict(X, verbose=0)
        y_proba = self.rf_model.predict_proba(X_encoded)[:, 1]
        y_pred = (y_proba > 0.5).astype(int)
        inference_time = time.time() - start_time
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'pr_auc': average_precision_score(y, y_proba) if len(np.unique(y)) > 1 else 0,
            'inference_time_per_sample': inference_time / len(X),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        X_encoded = self.encoder.predict(X, verbose=0)
        return self.rf_model.predict(X_encoded)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities"""
        X_encoded = self.encoder.predict(X, verbose=0)
        return self.rf_model.predict_proba(X_encoded)[:, 1]
    
    def save_model(self, path: str):
        """Save models"""
        # Save autoencoder
        ae_path = path.replace('.joblib', '_autoencoder.h5')
        self.autoencoder.save(ae_path)
        
        # Save RF
        rf_path = path.replace('.joblib', '_rf.joblib')
        joblib.dump(self.rf_model, rf_path)
        
        meta = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'encoding_dim': self.encoding_dim,
            'lstm_units': self.lstm_units,
            'rf_n_estimators': self.rf_n_estimators,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'training_time': self.training_time
        }
        meta_path = path.replace('.joblib', '_meta.json')
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        logger.info(f"LSTM-Autoencoder+RF saved to {path}")
    
    def load_model(self, path: str):
        """Load models"""
        ae_path = path.replace('.joblib', '_autoencoder.h5')
        rf_path = path.replace('.joblib', '_rf.joblib')
        
        self.autoencoder = tf.keras.models.load_model(ae_path)
        self.rf_model = joblib.load(rf_path)
        
        # Extract encoder
        self.encoder = Model(inputs=self.autoencoder.input,
                           outputs=self.autoencoder.get_layer(index=-4).output)
        
        meta_path = path.replace('.joblib', '_meta.json')
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                self.sequence_length = meta.get('sequence_length', 24)
                self.n_features = meta.get('n_features', 10)
                self.encoding_dim = meta.get('encoding_dim', 32)
                self.lstm_units = meta.get('lstm_units', 64)
                self.rf_n_estimators = meta.get('rf_n_estimators', 100)
                self.dropout_rate = meta.get('dropout_rate', 0.2)
                self.learning_rate = meta.get('learning_rate', 0.001)
                self.training_time = meta.get('training_time', 0)
        except FileNotFoundError:
            pass


def train_deep_models(X_train_seq, y_train_seq, X_val_seq, y_val_seq, 
                      n_features: int, sequence_length: int = 24) -> Dict:
    """Train both deep learning models"""
    results = {}
    models = {}
    
    if not HAS_TENSORFLOW:
        logger.warning("TensorFlow not installed. Deep learning models training skipped.")
        return results, models
    from sklearn.utils.class_weight import compute_class_weight
    classes = np.unique(y_train_seq)
    class_weights = compute_class_weight('balanced', classes=classes, y=y_train_seq)
    class_weight_dict = dict(zip(classes, class_weights))
    
    # CNN-LSTM
    logger.info("\n" + "="*50)
    logger.info("Training CNN-LSTM")
    logger.info("="*50)
    
    cnn_lstm = CNNLSTMModel(
        sequence_length=sequence_length,
        n_features=n_features,
        n_filters=64,
        lstm_units=64,
        dropout_rate=0.3,
        learning_rate=0.001
    )
    
    metrics = cnn_lstm.train(X_train_seq, y_train_seq, X_val_seq, y_val_seq,
                            epochs=50, batch_size=32, class_weight=class_weight_dict)
    
    cnn_lstm.save_model(str(settings.MODELS_DIR / "cnn_lstm_model.h5"))
    results['CNN-LSTM'] = metrics
    models['CNN-LSTM'] = cnn_lstm
    
    # LSTM-Autoencoder + RF
    logger.info("\n" + "="*50)
    logger.info("Training LSTM-Autoencoder + RF")
    logger.info("="*50)
    
    ae_rf = LSTMAutoencoderRF(
        sequence_length=sequence_length,
        n_features=n_features,
        encoding_dim=32,
        lstm_units=64,
        rf_n_estimators=200,
        dropout_rate=0.2,
        learning_rate=0.001
    )
    
    metrics = ae_rf.train_full(X_train_seq, y_train_seq, X_val_seq, y_val_seq,
                              epochs=50, batch_size=32)
    
    ae_rf.save_model(str(settings.MODELS_DIR / "lstm_ae_rf_model.joblib"))
    results['LSTM-Autoencoder+RF'] = metrics
    models['LSTM-Autoencoder+RF'] = ae_rf
    
    return results, models


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with dummy sequence data
    n_samples = 1000
    seq_len = 24
    n_feat = 10
    
    X = np.random.randn(n_samples, seq_len, n_feat)
    y = np.random.binomial(1, 0.1, n_samples)
    
    split = int(0.7 * n_samples)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    results, models = train_deep_models(X_train, y_train, X_val, y_val, n_feat, seq_len)
    
    for model_type, metrics in results.items():
        print(f"\n{model_type}:")
        for k, v in metrics.items():
            if k not in ['confusion_matrix']:
                print(f"  {k}: {v}")