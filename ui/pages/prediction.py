import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path
from config.settings import settings
from src.db.connection import db_pool
from src.preprocessing.preprocessor import DataPreprocessor
from ui.components import show_loading, show_success, show_error, show_info, paginated_dataframe

def render_prediction():
    st.markdown("## 🔮 Predicción en Tiempo Real - Fase 6 CRISP-DM")
    
    # Load best model
    if 'best_model' not in st.session_state:
        load_best_model()
    
    if 'best_model' not in st.session_state:
        show_error("No hay modelo entrenado disponible. Entrene modelos primero.")
        return
    
    model_info = st.session_state.best_model
    st.success(f"Modelo activo: **{model_info['name']}** (F1: {model_info['metrics'].get('f1_score', 0):.4f})")
    
    # Prediction mode
    tab1, tab2 = st.tabs(["📝 Entrada Manual", "📁 Cargar CSV"])
    
    with tab1:
        render_manual_prediction(model_info)
    
    with tab2:
        render_csv_prediction(model_info)
    
    # Scheduled predictions (simulation)
    st.markdown("---")
    render_scheduled_predictions()

def load_best_model():
    """Load the best model from disk"""
    models_dir = settings.MODELS_DIR
    
    # Try to find best model based on saved metrics
    best_model = None
    best_f1 = 0
    
    for meta_file in models_dir.glob("*_meta.json"):
        try:
            with open(meta_file) as f:
                meta = json.load(f)
            
            metrics = meta.get('metadata', {}).get('val_metrics', {})
            f1 = metrics.get('f1_score', 0)
            
            if f1 > best_f1:
                best_f1 = f1
                model_file = meta_file.with_name(meta_file.stem.replace('_meta', '') + '.joblib')
                if model_file.exists():
                    model = joblib.load(model_file)
                    best_model = {
                        'model': model,
                        'name': meta.get('model_type', 'Unknown'),
                        'metrics': metrics,
                        'path': str(model_file)
                    }
        except:
            continue
    
    if best_model:
        st.session_state.best_model = best_model
        # Also load preprocessor
        preprocessor_path = models_dir / "preprocessors.joblib"
        if preprocessor_path.exists():
            st.session_state.preprocessor = joblib.load(preprocessor_path)

def render_manual_prediction(model_info):
    """Manual sensor input for prediction"""
    st.markdown("### 📝 Entrada Manual de Lecturas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        temperatura = st.number_input("Temperatura (°C)", value=85.0, min_value=0.0, max_value=200.0)
        presion_aceite = st.number_input("Presión Aceite (PSI)", value=180.0, min_value=0.0, max_value=500.0)
        rpm = st.number_input("RPM", value=1800, min_value=0, max_value=5000)
    
    with col2:
        vibracion = st.number_input("Vibración (mm/s)", value=2.5, min_value=0.0, max_value=20.0)
        horas_operacion = st.number_input("Horas Operación", value=5000, min_value=0, max_value=100000)
        equipo_id = st.selectbox("Equipo", get_equipos_list())
    
    if st.button("🔮 Predecir", type="primary", use_container_width=True):
        with show_loading("Generando predicción..."):
            make_prediction(model_info, {
                'temperatura': temperatura,
                'presion_aceite': presion_aceite,
                'rpm': rpm,
                'vibracion': vibracion,
                'horas_operacion': horas_operacion
            }, equipo_id)

def render_csv_prediction(model_info):
    """Batch prediction from CSV"""
    st.markdown("### 📁 Predicción por Lotes (CSV)")
    
    uploaded_file = st.file_uploader("Subir archivo CSV con lecturas", type=['csv'])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Vista previa:")
        st.dataframe(df.head(), use_container_width=True)
        
        required_cols = ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            show_error(f"Faltan columnas requeridas: {missing}")
        else:
            if st.button("🔮 Predecir Lote", type="primary"):
                with show_loading(f"Procesando {len(df)} predicciones..."):
                    batch_predict(model_info, df)

def make_prediction(model_info, sensor_data: dict, equipo_id: int):
    """Make single prediction"""
    try:
        model = model_info['model']
        preprocessor = st.session_state.get('preprocessor')
        
        # Prepare features (simplified - in reality use full preprocessor)
        feature_order = ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']
        X = np.array([[sensor_data.get(f, 0) for f in feature_order]])
        
        # Apply preprocessing if available
        if preprocessor and 'scalers' in preprocessor:
            # This is simplified - real implementation would use the full pipeline
            pass
        
        # Predict
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(X)[0, 1]
            pred = model.predict(X)[0]
        else:
            proba = model.predict(X)[0]
            pred = int(proba > 0.5)
        
        # Display result
        st.markdown("---")
        st.markdown("### 📊 Resultado de la Predicción")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            status = "🔴 FALLA INMINENTE" if pred == 1 else "🟢 OPERACIÓN NORMAL"
            st.metric("Predicción", status)
        with col2:
            st.metric("Confianza", f"{proba:.2%}")
        with col3:
            st.metric("Riesgo", "ALTO" if proba > 0.7 else "MEDIO" if proba > 0.3 else "BAJO")
        
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=proba * 100,
            title={'text': "Probabilidad de Falla (%)"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "red" if proba > 0.5 else "green"},
                   'steps': [{'range': [0, 30], 'color': "lightgreen"},
                            {'range': [30, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "red"}],
                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 50}}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Save to database
        save_prediction(model_info, equipo_id, sensor_data, pred, proba)
        
    except Exception as e:
        show_error(f"Error en predicción: {e}")

def batch_predict(model_info, df: pd.DataFrame):
    """Batch prediction"""
    try:
        model = model_info['model']
        feature_order = ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']
        X = df[feature_order].values
        
        if hasattr(model, 'predict_proba'):
            probas = model.predict_proba(X)[:, 1]
            preds = model.predict(X)
        else:
            probas = model.predict(X).flatten()
            preds = (probas > 0.5).astype(int)
        
        # Add predictions to dataframe
        df['falla_predicha'] = preds
        df['confianza'] = probas
        df['riesgo'] = pd.cut(probas, bins=[0, 0.3, 0.7, 1], labels=['BAJO', 'MEDIO', 'ALTO'])
        
        show_success(f"Predicciones completadas: {preds.sum()} fallas predichas de {len(preds)}")
        
        # Show results
        st.dataframe(df[['falla_predicha', 'confianza', 'riesgo'] + feature_order].head(20), use_container_width=True)
        
        # Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Resultados", csv, "predicciones_lote.csv", "text/csv")
        
        # Save to database (first row's equipo_id or default)
        equipo_id = df.get('equipo_id', [1])[0] if 'equipo_id' in df.columns else 1
        for idx, row in df.iterrows():
            save_prediction(model_info, equipo_id, row[feature_order].to_dict(), 
                          row['falla_predicha'], row['confianza'])
        
    except Exception as e:
        show_error(f"Error en predicción por lotes: {e}")

def save_prediction(model_info, equipo_id: int, sensor_data: dict, pred: int, proba: float):
    """Save prediction to database"""
    try:
        from src.auth.auth_service import auth_service
        user_id = st.session_state.user['id'] if st.session_state.user else None
        
        query = """
            INSERT INTO predicciones (equipo_id, modelo_id, falla_predicha, confianza, datos_entrada, usuario_ejecutor)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        # Get model ID from database (simplified - use 1 for demo)
        modelo_id = 1
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (equipo_id, modelo_id, bool(pred), proba, json.dumps(sensor_data), user_id))
            pred_id = cursor.fetchone()['id']
        
        show_info(f"Predicción guardada con ID: {pred_id}")
        
    except Exception as e:
        show_warning(f"No se pudo guardar en BD: {e}")

def render_scheduled_predictions():
    """Simulated scheduled predictions"""
    st.markdown("### ⏰ Predicciones Programadas (Simulación)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Ejecutar Ahora"):
            with show_loading("Ejecutando predicción programada..."):
                time.sleep(2)
                show_success("Predicción programada ejecutada")
    
    with col2:
        st.selectbox("Frecuencia", ["Cada hora", "Cada 6 horas", "Diario"])
    
    with col3:
        st.selectbox("Equipos", ["Todos los activos", "Solo críticos"])

def get_equipos_list():
    """Get active equipment list"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT id, codigo FROM equipos WHERE estado = 'activo' ORDER BY codigo")
            return [f"{row['codigo']} (ID: {row['id']})" for row in cursor.fetchall()]
    except:
        return ["EQP-001 (ID: 1)", "EQP-002 (ID: 2)"]

if __name__ == "__main__":
    render_prediction()