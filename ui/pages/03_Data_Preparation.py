import streamlit as st
import pandas as pd
import numpy as np
from ui.components import render_crisp_dm_phase_indicator, show_loading, show_success, show_error, show_info
from src.preprocessing.preprocessor import prepare_training_data

def render_data_preparation():
    render_crisp_dm_phase_indicator(3)

    st.markdown("## 🧹 Fase 3: Preparación de Datos y Feature Engineering")
    st.caption("Estructuración del pipeline de transformación: limpieza, ingeniería de variables derivadas y partición balanceada para modelado predictivo.")

    # Architecture Pipeline Visual Cards
    st.markdown("### ⚙️ Arquitectura del Pipeline de Datos")
    
    p_cols = st.columns(4)
    with p_cols[0]:
        st.markdown(
            """
            <div class="unt-card" style="height:100%;">
                <div style="font-size:1.5rem; margin-bottom:6px;">📥 1. Ingesta</div>
                <strong>Pivoteo Temporal</strong>
                <p style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Lecturas continuas de sensores reordenadas en matriz temporal unificada por equipo.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p_cols[1]:
        st.markdown(
            """
            <div class="unt-card" style="height:100%;">
                <div style="font-size:1.5rem; margin-bottom:6px;">🧼 2. Limpieza</div>
                <strong>Imputación & Outliers</strong>
                <p style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Reemplazo de nulos por mediana y filtrado de señales espurias mediante umbrales IQR.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p_cols[2]:
        st.markdown(
            """
            <div class="unt-card" style="height:100%;">
                <div style="font-size:1.5rem; margin-bottom:6px;">🔬 3. Features</div>
                <strong>Rolling Stats</strong>
                <p style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Medias y desvíos móviles (6h, 12h, 24h) para capturar tendencias de degradación mecánica.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with p_cols[3]:
        st.markdown(
            """
            <div class="unt-card" style="height:100%;">
                <div style="font-size:1.5rem; margin-bottom:6px;">🎯 4. Target</div>
                <strong>Etiquetado 24h</strong>
                <p style="font-size:0.75rem; color:#64748B; margin-top:4px;">
                    Definición de falla binaria (0/1) con horizonte anticipatorio de 24 horas previas.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Feature Engineering Specification Table
    st.markdown("### 📐 Diccionario de Variables Derivadas (Feature Engineering)")
    fe_df = pd.DataFrame([
        {"Variable Base": "temperatura", "Transformación": "Media móvil (Rolling 6h, 12h, 24h)", "Propósito": "Detecta calentamiento acumulado del motor."},
        {"Variable Base": "vibracion", "Transformación": "Desviación estándar móvil (Rolling 12h)", "Propósito": "Captura fluctuaciones y desalineación estructural."},
        {"Variable Base": "presion_aceite", "Transformación": "Gradiente diferencial (ΔP / Δt)", "Propósito": "Identifica caídas abruptas de presión hidráulica."},
        {"Variable Base": "rpm & vibración", "Transformación": "Ratio Vibración / RPM", "Propósito": "Normaliza la vibración mecánica según el régimen operativo."},
        {"Variable Base": "horas_operacion", "Transformación": "Escalado MinMax normalizado", "Propósito": "Pondera el desgaste progresivo en la escala [0, 1]."}
    ])
    st.dataframe(fe_df, use_container_width=True, hide_index=True)

    st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Execution & Dataset Generation
    st.markdown("### 🚀 Ejecución del Pipeline y Partición de Datos")
    st.write("Procese la telemetría en memoria para generar los conjuntos de Entrenamiento, Validación y Test.")

    btn_col1, btn_col2 = st.columns([1, 2])
    with btn_col1:
        if st.button("🔄 Procesar y Preparar Dataset", type="primary", use_container_width=True):
            with show_loading("Ejecutando pipeline de preparación... Esto toma pocos segundos"):
                try:
                    train_df, val_df, test_df = prepare_training_data()
                    st.session_state.train_data = (train_df, val_df, test_df)
                    show_success("¡Pipeline ejecutado exitosamente!")
                except Exception as e:
                    show_error(f"Error procesando datos: {e}")

    if 'train_data' in st.session_state:
        train_df, val_df, test_df = st.session_state.train_data
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Muestras", f"{len(train_df) + len(val_df) + len(test_df):,}")
        with m2:
            st.metric("Entrenamiento (Train)", f"{len(train_df):,} (70%)")
        with m3:
            st.metric("Validación (Val)", f"{len(val_df):,} (15%)")
        with m4:
            st.metric("Prueba (Test)", f"{len(test_df):,} (15%)")

        st.markdown("#### Vista Previa del Dataset Procesado (Primeras filas de Entrenamiento)")
        st.dataframe(train_df.head(10), use_container_width=True)

        # Download button
        csv_data = train_df.head(1000).to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Muestra del Dataset Procesado (CSV)",
            csv_data,
            file_name="dataset_procesado_unt.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        show_info("Haga clic en 'Procesar y Preparar Dataset' para compilar las variables y visualizar el conjunto particionado.")
