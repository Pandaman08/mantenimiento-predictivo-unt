import streamlit as st
import pandas as pd
from ui.components import render_crisp_dm_phase_indicator, render_metric_card

def render_business_understanding():
    render_crisp_dm_phase_indicator(1)

    st.markdown("## 🏢 Fase 1: Comprensión del Negocio y Objetivos Estratégicos")
    st.caption("Alineación entre los retos de la industria minera, la reducción de paradas no programadas y los criterios de éxito del modelo predictivo.")

    # Strategic Objectives Cards
    st.markdown("### 🎯 Objetivos Estratégicos de Operación")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Reducción MTTR",
            value="-20.0%",
            delta="Objetivo: 10.0h",
            delta_positive=True,
            icon="⏱️",
            subtitle="Tiempo medio de reparación en averías"
        )
    with c2:
        render_metric_card(
            title="Incremento Disponibilidad",
            value="+5.0%",
            delta="Meta: >99.0%",
            delta_positive=True,
            icon="📈",
            subtitle="Maximización del tiempo productivo de flota"
        )
    with c3:
        render_metric_card(
            title="Reducción Costos Mantenimiento",
            value="-15.0%",
            delta="Ahorro: S/ 96,000/año",
            delta_positive=True,
            icon="💰",
            subtitle="Disminución de paradas de emergencia críticas"
        )

    st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Interactive ROI & Downtime Calculator
    st.markdown("### 🧮 Calculadora Interactiva de Impacto Económico y ROI")
    st.write("Estime el retorno de inversión y el ahorro anual al evitar fallas catastróficas en palas y camiones de acarreo.")

    with st.container():
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            num_equipos = st.slider("Tamaño de flota monitoreada", min_value=1, max_value=25, value=5, step=1)
            fallas_anuales = st.slider("Fallas imprevistas por equipo/año", min_value=1, max_value=20, value=6, step=1)
        with rc2:
            costo_hora_parada = st.number_input("Costo de parada no programada ($/hora)", min_value=200, max_value=10000, value=1500, step=100)
            horas_reparacion_prom = st.number_input("Horas de reparación por falla", min_value=1.0, max_value=48.0, value=12.5, step=0.5)
        with rc3:
            tasa_exito_ia = st.slider("Tasa de anticipación del modelo IA (%)", min_value=50, max_value=99, value=88, step=1)

        # Calculations
        costo_total_actual = num_equipos * fallas_anuales * horas_reparacion_prom * costo_hora_parada
        fallas_evitadas = (num_equipos * fallas_anuales) * (tasa_exito_ia / 100.0)
        ahorro_estimado = fallas_evitadas * horas_reparacion_prom * costo_hora_parada

        st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:0.8rem 0;'>", unsafe_allow_html=True)

        res_c1, res_c2, res_c3 = st.columns(3)
        with res_c1:
            st.metric("Costo Anual por Paradas Actuales", f"${costo_total_actual:,.0f} USD")
        with res_c2:
            st.metric("Fallas Críticas Evitadas", f"{fallas_evitadas:.1f} eventos/año", delta=f"{tasa_exito_ia}% Efectividad")
        with res_c3:
            st.metric("Ahorro Estimado Anual", f"${ahorro_estimado:,.0f} USD", delta=f"+{ahorro_estimado/costo_total_actual*100:.1f}% ROI")

        # closing wrapper removed to avoid rendering literal tags
        st.markdown("", unsafe_allow_html=True)

    st.markdown("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1.5rem 0;'>", unsafe_allow_html=True)

    # Comparison Table & Success Criteria
    t_col1, t_col2 = st.columns([1.1, 1], gap="medium")

    with t_col1:
        st.markdown("### 📊 Estado Base Operacional vs. Metas")
        comparison_df = pd.DataFrame([
            {"Indicador": "MTTR (Tiempo Medio Reparación)", "Línea Base": "12.5 horas", "Meta 2026": "10.0 horas", "Variación": "-20%"},
            {"Indicador": "Disponibilidad de Flota", "Línea Base": "94.0%", "Meta 2026": "99.0%", "Variación": "+5.0%"},
            {"Indicador": "Costo de Parada Anual", "Línea Base": "S/ 640,000", "Meta 2026": "S/ 544,000", "Variación": "-15.0%"},
            {"Indicador": "Frecuencia Mantenimiento Correctivo", "Línea Base": "32 eventos", "Meta 2026": "<10 eventos", "Variación": "-68.7%"}
        ])
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

    with t_col2:
        st.markdown("### 🎯 Criterios de Éxito del Modelo de IA")
        criteria_df = pd.DataFrame([
            {"Métrica IA": "F1-Score Global", "Requisito Mínimo": "≥ 0.88", "Estado": "✅ Superado (0.95)"},
            {"Métrica IA": "Sensibilidad (Recall)", "Requisito Mínimo": "≥ 85.0%", "Estado": "✅ Superado (91.5%)"},
            {"Métrica IA": "Precisión (Evitar Falsas Alarmas)", "Requisito Mínimo": "≥ 90.0%", "Estado": "✅ Superado (93.0%)"},
            {"Métrica IA": "Tiempo de Inferencia", "Requisito Mínimo": "< 1.0 seg", "Estado": "✅ Óptimo (0.08 seg)"}
        ])
        st.dataframe(criteria_df, use_container_width=True, hide_index=True)
