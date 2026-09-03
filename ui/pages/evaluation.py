import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import joblib
import json
from pathlib import Path
from config.settings import settings
from src.evaluation.evaluator import compare_all_models
from src.preprocessing.preprocessor import prepare_training_data
from ui.components import (render_crisp_dm_phase_indicator, show_loading, show_error, show_success,
                          plot_confusion_matrix, plot_roc_curve, paginated_dataframe)

def render_evaluation():
    render_crisp_dm_phase_indicator(5)
    
    st.markdown("## 📊 Evaluación Comparativa - Fase 5 CRISP-DM")
    
    # Load test data and models
    if st.button("🔄 Cargar Datos de Test y Modelos", type="primary"):
        with show_loading("Preparando datos de evaluación..."):
            load_evaluation_data()
    
    if 'eval_data' not in st.session_state:
        show_info("Haga clic en 'Cargar Datos de Test y Modelos' para comenzar")
        return
    
    models = st.session_state.eval_models
    X_test = st.session_state.eval_data['X_test']
    y_test = st.session_state.eval_data['y_test']
    X_train = st.session_state.eval_data.get('X_train')
    y_train = st.session_state.eval_data.get('y_train')
    
    if not models:
        show_error("No se encontraron modelos entrenados")
        return
    
    st.success(f"Modelos cargados: {len(models)} | Test samples: {len(X_test)}")
    
    # Run evaluation
    if st.button("🚀 Ejecutar Evaluación Completa", type="primary"):
        with show_loading("Evaluando modelos... Esto puede tomar unos minutos"):
            run_full_evaluation(models, X_test, y_test, X_train, y_train)
    
    # Show results if available
    if 'eval_results' in st.session_state:
        show_evaluation_results(st.session_state.eval_results)

def load_evaluation_data():
    """Load test data and trained models"""
    try:
        # Load test data
        train_df, val_df, test_df = prepare_training_data()
        
        target_col = 'falla'
        exclude_cols = [target_col, 'equipo_id', 'timestamp', 'equipo_codigo', 'equipo_tipo']
        feature_cols = [c for c in test_df.columns if c not in exclude_cols]
        
        X_test = test_df[feature_cols].values
        y_test = test_df[target_col].values
        X_train = train_df[feature_cols].values
        y_train = train_df[target_col].values
        
        # Load models
        models = {}
        models_dir = settings.MODELS_DIR
        
        # Traditional models
        for model_file in models_dir.glob("*_model.joblib"):
            if 'cnn' not in model_file.name and 'lstm' not in model_file.name:
                try:
                    model_name = model_file.stem.replace('_model', '').replace('_', ' ').title()
                    model = joblib.load(model_file)
                    models[model_name] = model
                except Exception as e:
                    st.warning(f"No se pudo cargar {model_file.name}: {e}")
        
        # Deep models (if available)
        try:
            import tensorflow as tf
            for model_file in models_dir.glob("*_model.h5"):
                model_name = model_file.stem.replace('_model', '').replace('_', ' ').title()
                model = tf.keras.models.load_model(model_file)
                models[model_name] = model
        except:
            pass
        
        st.session_state.eval_data = {
            'X_test': X_test, 'y_test': y_test,
            'X_train': X_train, 'y_train': y_train,
            'feature_cols': feature_cols
        }
        st.session_state.eval_models = models
        
    except Exception as e:
        show_error(f"Error cargando datos: {e}")

def run_full_evaluation(models, X_test, y_test, X_train, y_train):
    """Run complete evaluation with statistical tests"""
    try:
        # Wrap models for evaluator
        wrapped_models = {}
        for name, model in models.items():
            if hasattr(model, 'predict'):
                wrapped_models[name] = model
            else:
                # Keras model wrapper
                class KerasWrapper:
                    def __init__(self, m): self.m = m
                    def predict(self, X): return (self.m.predict(X, verbose=0) > 0.5).astype(int).flatten()
                    def predict_proba(self, X): 
                        proba = self.m.predict(X, verbose=0).flatten()
                        return np.column_stack([1-proba, proba])
                wrapped_models[name] = KerasWrapper(model)
        
        results = compare_all_models(wrapped_models, X_test, y_test, X_train, y_train)
        st.session_state.eval_results = results
        show_success("Evaluación completada!")
        
    except Exception as e:
        show_error(f"Error en evaluación: {e}")

def show_evaluation_results(results: dict):
    """Display comprehensive evaluation results"""
    st.markdown("---")
    
    # Best model highlight
    best_model = results['best_model']
    st.success(f"🏆 **Mejor modelo global: {best_model}**")
    
    # Comparison Table
    st.markdown("### 📋 Tabla Comparativa de Métricas")
    comp_df = pd.DataFrame(results['comparison_table'])
    st.dataframe(comp_df.style.highlight_max(axis=0, subset=['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'pr_auc']),
                use_container_width=True, hide_index=True)
    
    # Metrics visualization
    st.markdown("### 📈 Visualización de Métricas")
    
    metrics_to_plot = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 'pr_auc']
    fig = go.Figure()
    
    for metric in metrics_to_plot:
        values = [r.get(metric, 0) for r in results['comparison_table']]
        names = [r['Model'] for r in results['comparison_table']]
        fig.add_trace(go.Bar(name=metric.upper(), x=names, y=values))
    
    fig.update_layout(barmode='group', title="Comparación de Métricas", template='plotly_white', height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Confusion Matrices
    st.markdown("### 🎯 Matrices de Confusión")
    cm_cols = st.columns(min(3, len(results['test_metrics'])))
    for i, (name, metrics) in enumerate(results['test_metrics'].items()):
        with cm_cols[i % 3]:
            cm = metrics.get('confusion_matrix', [[0,0],[0,0]])
            fig = plot_confusion_matrix(cm, title=f"{name}")
            st.plotly_chart(fig, use_container_width=True)
    
    # Cross-validation results
    st.markdown("### 🔄 Validación Cruzada")
    cv_tab1, cv_tab2 = st.tabs(["Time Series Split", "Stratified K-Fold"])
    
    with cv_tab1:
        show_cv_results(results['cross_validation_timeseries'], "Time Series")
    
    with cv_tab2:
        show_cv_results(results['cross_validation_stratified'], "Stratified")
    
    # Statistical Tests
    st.markdown("### 📐 Pruebas Estadísticas Comparativas")
    
    st.markdown("#### Test t Pareado (F1-Score)")
    t_test_df = pd.DataFrame([{
        'Modelo A': t['model1'],
        'Modelo B': t['model2'],
        't-statistic': f"{t['t_statistic']:.4f}",
        'p-value': f"{t['p_value']:.6f}",
        'Significativo': '✅' if t['significant'] else '❌',
        'Diferencia Media': f"{t['mean_diff']:.4f}"
    } for t in results['paired_t_tests'] if t['metric'] == 'f1_score'])
    st.dataframe(t_test_df, use_container_width=True, hide_index=True)
    
    st.markdown("#### Test de McNemar")
    mcnemar_df = pd.DataFrame([{
        'Modelo A': m['model1'],
        'Modelo B': m['model2'],
        'χ²': f"{m['chi2_statistic']:.4f}",
        'p-value': f"{m['p_value']:.6f}",
        'Significativo': '✅' if m['significant'] else '❌'
    } for m in results['mcnemar_tests']])
    st.dataframe(mcnemar_df, use_container_width=True, hide_index=True)
    
    # Bootstrap Confidence Intervals
    st.markdown("### 📊 Intervalos de Confianza (Bootstrap)")
    for name, cis in results['bootstrap_cis'].items():
        with st.expander(f"{name}"):
            ci_df = pd.DataFrame([{
                'Métrica': m,
                'Media': f"{v['mean']:.4f}",
                'Std': f"{v['std']:.4f}",
                'CI 95% Inferior': f"{v['ci_lower']:.4f}",
                'CI 95% Superior': f"{v['ci_upper']:.4f}"
            } for m, v in cis.items()])
            st.dataframe(ci_df, use_container_width=True, hide_index=True)
    
    # Noise Sensitivity
    st.markdown("### 🔊 Sensibilidad al Ruido")
    noise_data = []
    for name, sensitivities in results['noise_sensitivity'].items():
        for noise_level, metrics in sensitivities.items():
            noise_data.append({
                'Modelo': name,
                'Nivel Ruido': noise_level,
                'F1-Score': f"{metrics['f1_score']:.4f}",
                'Degradación': f"{metrics['degradation']:.2%}"
            })
    
    if noise_data:
        noise_df = pd.DataFrame(noise_data)
        fig = px.line(noise_df, x='Nivel Ruido', y='F1-Score', color='Modelo', markers=True,
                     title="Degradación del Rendimiento con Ruido Gaussiano")
        fig.update_layout(template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(noise_df, use_container_width=True, hide_index=True)

def show_cv_results(cv_results: dict, title: str):
    """Show cross-validation results"""
    if not cv_results:
        show_info(f"No hay resultados de {title}")
        return
    
    rows = []
    for model_name, metrics in cv_results.items():
        row = {'Modelo': model_name}
        for metric_name, values in metrics.items():
            row[f'{metric_name}_mean'] = f"{values['mean']:.4f}"
            row[f'{metric_name}_std'] = f"{values['std']:.4f}"
        rows.append(row)
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    render_evaluation()