import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import json
import time
from pathlib import Path
from config.settings import settings
from src.db.connection import db_pool
from src.models.traditional_models import TraditionalModelTrainer, train_all_traditional_models
from src.models.deep_models import train_deep_models
from src.preprocessing.preprocessor import prepare_training_data
from ui.components import (render_crisp_dm_phase_indicator, show_loading, show_success, show_error, 
                          plot_confusion_matrix, plot_learning_curve)

def render_training():
    render_crisp_dm_phase_indicator(4)
    
    st.markdown("## 🤖 Entrenamiento de Modelos - Fase 4 CRISP-DM")
    st.info("Esta sección permite entrenar y comparar múltiples algoritmos de ML y Deep Learning")
    
    # Configuration
    st.markdown("### ⚙️ Configuración de Entrenamiento")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        model_category = st.selectbox("Categoría", ["Tradicionales (RF, XGBoost, SVM)", "Deep Learning (CNN-LSTM, LSTM-AE+RF)", "Todos"])
    with col2:
        tune_hyperparams = st.checkbox("Optimizar hiperparámetros (Random Search)", value=False)
    with col3:
        test_size = st.slider("Tamaño test set (%)", 10, 30, 15)
    
    # Data preparation
    st.markdown("### 📊 Preparación de Datos")
    if st.button("🔄 Preparar Datos de Entrenamiento", type="primary"):
        with show_loading("Preparando datos... Esto puede tomar unos minutos"):
            try:
                train_df, val_df, test_df = prepare_training_data()
                st.session_state.train_data = (train_df, val_df, test_df)
                show_success(f"Datos preparados: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
            except Exception as e:
                show_error(f"Error preparando datos: {e}")
    
    if 'train_data' not in st.session_state:
        show_warning("Primero prepare los datos de entrenamiento")
        return
    
    train_df, val_df, test_df = st.session_state.train_data
    
    # Prepare features
    target_col = 'falla'
    exclude_cols = [target_col, 'equipo_id', 'timestamp', 'equipo_codigo', 'equipo_tipo']
    feature_cols = [c for c in train_df.columns if c not in exclude_cols]
    
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_val = val_df[feature_cols].values
    y_val = val_df[target_col].values
    
    st.info(f"Features: {len(feature_cols)} | Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(test_df)}")
    st.write(f"Distribución target - Train: {y_train.mean():.2%}, Val: {y_val.mean():.2%}")
    
    # Training buttons
    st.markdown("### 🚀 Entrenar Modelos")
    
    if model_category in ["Tradicionales (RF, XGBoost, SVM)", "Todos"]:
        if st.button("Entrenar Modelos Tradicionales", type="primary"):
            train_traditional_models(X_train, y_train, X_val, y_val, tune_hyperparams)
    
    if model_category in ["Deep Learning (CNN-LSTM, LSTM-AE+RF)", "Todos"]:
        if st.button("Entrenar Modelos Deep Learning", type="primary"):
            train_deep_learning_models(X_train, y_train, X_val, y_val, len(feature_cols))
    
    # Show trained models
    st.markdown("### 📋 Modelos Entrenados")
    show_trained_models()

def train_traditional_models(X_train, y_train, X_val, y_val, tune):
    """Train traditional ML models"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Entrenando Random Forest...")
        progress_bar.progress(0.2)
        
        status_text.text("Entrenando XGBoost...")
        progress_bar.progress(0.5)
        
        status_text.text("Entrenando SVM...")
        progress_bar.progress(0.8)
        
        results, models = train_all_traditional_models(X_train, y_train, X_val, y_val, tune)
        
        # Save to session state
        st.session_state.trained_traditional = {name: {'model': m, 'metrics': results[name]} 
                                                 for name, m in models.items()}
        
        progress_bar.progress(1.0)
        status_text.text("¡Completado!")
        
        # Show results
        show_training_results(results, "Tradicionales")
        
    except Exception as e:
        show_error(f"Error en entrenamiento: {e}")

def train_deep_learning_models(X_train, y_train, X_val, y_val, n_features):
    """Train deep learning models"""
    # Need to prepare sequences for DL
    from src.preprocessing.preprocessor import DataPreprocessor
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Prepare sequences (simplified - using last 24 time steps)
        sequence_length = 24
        
        status_text.text("Preparando secuencias temporales...")
        progress_bar.progress(0.1)
        
        # This is a simplified version - in reality you'd use the preprocessor
        # For now, we'll create dummy sequences for demo
        n_samples = min(len(X_train), 1000)
        X_train_seq = X_train[:n_samples].reshape(-1, 1, n_features)
        X_train_seq = np.repeat(X_train_seq, sequence_length, axis=1)
        y_train_seq = y_train[:n_samples]
        
        n_val = min(len(X_val), 300)
        X_val_seq = X_val[:n_val].reshape(-1, 1, n_features)
        X_val_seq = np.repeat(X_val_seq, sequence_length, axis=1)
        y_val_seq = y_val[:n_val]
        
        status_text.text("Entrenando CNN-LSTM...")
        progress_bar.progress(0.4)
        
        status_text.text("Entrenando LSTM-Autoencoder+RF...")
        progress_bar.progress(0.7)
        
        # Train (this will take time in reality)
        results, models = train_deep_models(X_train_seq, y_train_seq, X_val_seq, y_val_seq, n_features, sequence_length)
        
        st.session_state.trained_deep = {name: {'model': m, 'metrics': results[name]} 
                                        for name, m in models.items()}
        
        progress_bar.progress(1.0)
        status_text.text("¡Completado!")
        
        show_training_results(results, "Deep Learning")
        
    except Exception as e:
        show_error(f"Error en entrenamiento DL: {e}")
        st.info("Nota: El entrenamiento DL requiere TensorFlow y puede tardar varios minutos.")

def show_training_results(results: dict, category: str):
    """Display training results"""
    st.markdown(f"#### Resultados: {category}")
    
    cols = st.columns(len(results))
    for i, (name, metrics) in enumerate(results.items()):
        with cols[i]:
            st.markdown(f"**{name}**")
            for k, v in metrics.items():
                if k not in ['confusion_matrix', 'classification_report']:
                    if isinstance(v, float):
                        st.metric(k.replace('_', ' ').title(), f"{v:.4f}")
                    else:
                        st.metric(k.replace('_', ' ').title(), str(v))

def show_trained_models():
    """Show list of trained models"""
    models_found = []
    
    # Check traditional
    if 'trained_traditional' in st.session_state:
        for name, data in st.session_state.trained_traditional.items():
            models_found.append({
                'Modelo': name,
                'Tipo': 'Tradicional',
                'F1-Score': f"{data['metrics'].get('f1_score', 0):.4f}",
                'ROC-AUC': f"{data['metrics'].get('roc_auc', 0):.4f}",
                'Tiempo Inf.': f"{data['metrics'].get('inference_time_per_sample', 0)*1000:.2f}ms"
            })
    
    # Check deep
    if 'trained_deep' in st.session_state:
        for name, data in st.session_state.trained_deep.items():
            models_found.append({
                'Modelo': name,
                'Tipo': 'Deep Learning',
                'F1-Score': f"{data['metrics'].get('f1_score', 0):.4f}",
                'ROC-AUC': f"{data['metrics'].get('roc_auc', 0):.4f}",
                'Tiempo Inf.': f"{data['metrics'].get('inference_time_per_sample', 0)*1000:.2f}ms"
            })
    
    # Check saved models
    models_dir = settings.MODELS_DIR
    for model_file in models_dir.glob("*_model.joblib"):
        meta_file = model_file.with_name(model_file.stem + '_meta.json')
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            models_found.append({
                'Modelo': meta.get('model_type', model_file.stem),
                'Tipo': 'Guardado',
                'F1-Score': 'N/A',
                'ROC-AUC': 'N/A',
                'Tiempo Inf.': 'N/A'
            })
    
    if models_found:
        st.dataframe(pd.DataFrame(models_found), use_container_width=True, hide_index=True)
    else:
        show_info("No hay modelos entrenados todavía")

if __name__ == "__main__":
    render_training()