import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from src.db.connection import db_pool
from ui.components import (
    plot_histogram, plot_boxplot, plot_correlation_heatmap,
    plot_scatter_matrix, paginated_dataframe,
    render_crisp_dm_phase_indicator, show_loading, show_info,
    UNT_PRIMARY, UNT_GOLD, UNT_WARNING, UNT_DANGER, apply_plotly_theme
)

def render_eda():
    render_crisp_dm_phase_indicator(2)

    st.markdown("## 📈 Fase 2: Comprensión y Exploración de Datos (EDA)")
    st.caption("Inspección estadística, verificación de calidad de telemetría y correlaciones dinámicas entre variables de maquinaria pesada.")

    # Load data
    with show_loading("Cargando y pivotando datos de sensores para EDA..."):
        df = load_eda_data()

    if df.empty:
        st.warning("No hay datos de telemetría disponibles en la base de datos.")
        return

    # In-page Filter Bar
    with st.expander("🔍 Filtros de Exploración de Datos", expanded=True):
        f1, f2 = st.columns([1, 1])
        with f1:
            equipos_disp = ["Todos"] + sorted(df['equipo_codigo'].dropna().unique().tolist())
            equipo_filter = st.selectbox("Seleccionar Equipo", equipos_disp, index=0)
        with f2:
            min_date = df['timestamp'].min().date() if pd.notnull(df['timestamp'].min()) else None
            max_date = df['timestamp'].max().date() if pd.notnull(df['timestamp'].max()) else None
            date_range = st.date_input(
                "Rango de Fechas de Operación",
                value=(min_date, max_date) if min_date and max_date else None
            )

    # Apply filters
    filtered_df = df.copy()
    if equipo_filter != "Todos":
        filtered_df = filtered_df[filtered_df['equipo_codigo'] == equipo_filter]
    if date_range and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['timestamp'].dt.date >= date_range[0]) &
            (filtered_df['timestamp'].dt.date <= date_range[1])
        ]

    st.info(f"📊 Registros analizados: **{len(filtered_df):,}** de {len(df):,} muestras temporales")

    # Tabs for different analyses
    tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 Diccionario de Variables",
        "📊 Estadísticas Descriptivas",
        "📈 Distribuciones",
        "🔗 Correlaciones",
        "🎯 Detección de Outliers",
        "📋 Datos Filtrados"
    ])

    with tab0:
        render_data_dictionary()

    with tab1:
        render_descriptive_stats(filtered_df)

    with tab2:
        render_distributions(filtered_df)

    with tab3:
        render_correlations(filtered_df)

    with tab4:
        render_outliers(filtered_df)

    with tab5:
        render_filtered_data(filtered_df)


def render_data_dictionary():
    """Render variable dictionary and quality summary"""
    st.markdown("### 📖 Diccionario de Variables y Calidad de Telemetría")

    vars_info = [
        {"Variable": "temperatura", "Unidad": "°C", "Rango Nominal": "70 - 105 °C", "Criticidad": "🔴 Muy Alta", "Descripción": "Temperatura del motor y sistema de transmisión. Aumentos sostenidos indican sobrecarga o fallo de refrigeración."},
        {"Variable": "presion_aceite", "Unidad": "PSI", "Rango Nominal": "150 - 240 PSI", "Criticidad": "🔴 Muy Alta", "Descripción": "Presión del lubricante hidráulico y motor. Caídas abruptas preceden roturas de sellos o cavitación."},
        {"Variable": "rpm", "Unidad": "RPM", "Rango Nominal": "1400 - 2100 RPM", "Criticidad": "🟡 Media", "Descripción": "Velocidad angular del eje motor. Mide régimen de trabajo y exigencia de torque mecánico."},
        {"Variable": "vibracion", "Unidad": "mm/s", "Rango Nominal": "1.0 - 4.5 mm/s", "Criticidad": "🔴 Muy Alta", "Descripción": "Amplitud espectral de vibraciones. Es el indicador principal de desbalance, desalineación o fatiga de rodamientos."},
        {"Variable": "horas_operacion", "Unidad": "Horas", "Rango Nominal": "0 - 25,000 h", "Criticidad": "🟢 Baja", "Descripción": "Tiempo acumulado de servicio del equipo minero. Se utiliza para modelar degradación acumulada."}
    ]
    st.dataframe(pd.DataFrame(vars_info), use_container_width=True, hide_index=True)


def load_eda_data():
    """Load data for EDA - pivoted format"""
    try:
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
            WHERE e.estado = 'activo' AND s.activo = true
            ORDER BY e.id, l.timestamp
            LIMIT 50000
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Pivot to wide format
        df_pivot = df.pivot_table(
            index=['timestamp', 'equipo_id', 'equipo_codigo', 'equipo_tipo'],
            columns='tipo_sensor',
            values='valor',
            aggfunc='mean'
        ).reset_index()
        df_pivot.columns.name = None
        df_pivot['timestamp'] = pd.to_datetime(df_pivot['timestamp'])

        return df_pivot
    except Exception as e:
        st.error(f"Error cargando datos EDA: {e}")
        return pd.DataFrame()


def render_descriptive_stats(df: pd.DataFrame):
    """Render descriptive statistics"""
    st.markdown("### 📊 Métricas Estadísticas de Sensores")

    sensor_cols = [c for c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion'] if c in df.columns]

    if not sensor_cols:
        st.warning("No hay columnas de sensores disponibles")
        return

    stats_df = df[sensor_cols].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T
    stats_df = stats_df.round(2)
    st.dataframe(stats_df, use_container_width=True)

    st.markdown("#### Distribución Estadística por Tipo de Maquinaria")
    if 'equipo_tipo' in df.columns:
        for eq_type in df['equipo_tipo'].dropna().unique():
            with st.expander(sanitize_text(f"🚜 Maquinaria: {eq_type.capitalize()}")):
                eq_df = df[df['equipo_tipo'] == eq_type][sensor_cols]
                if not eq_df.empty:
                    st.dataframe(eq_df.describe().T.round(2), use_container_width=True)


def render_distributions(df: pd.DataFrame):
    """Render distribution plots"""
    st.markdown("### 📈 Histogramas y Boxplots de Variables Telemétricas")

    sensor_cols = [c for c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion'] if c in df.columns]
    if not sensor_cols:
        return

    col1, col2 = st.columns(2)
    with col1:
        selected_sensor = st.selectbox("Sensor para análisis", sensor_cols, index=0)
        fig_hist = plot_histogram(
            df, selected_sensor,
            color='equipo_tipo' if 'equipo_tipo' in df.columns else None,
            title=f"Histograma de {selected_sensor.replace('_', ' ').capitalize()}"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        fig_box = plot_boxplot(
            df,
            'equipo_tipo' if 'equipo_tipo' in df.columns else 'equipo_codigo',
            selected_sensor,
            title=f"Boxplot de {selected_sensor.replace('_', ' ').capitalize()} por Equipo"
        )
        st.plotly_chart(fig_box, use_container_width=True)


def render_correlations(df: pd.DataFrame):
    """Render correlation analysis"""
    st.markdown("### 🔗 Matriz de Correlación Inter-Sensorial")
    sensor_cols = [c for c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion'] if c in df.columns]

    if len(sensor_cols) < 2:
        show_info("Insuficientes columnas numéricas para correlación.")
        return

    fig = plot_correlation_heatmap(df[sensor_cols], "Matriz de Correlación de Pearson")
    st.plotly_chart(fig, use_container_width=True)


def render_outliers(df: pd.DataFrame):
    """Render outlier detection"""
    st.markdown("### 🎯 Detección y Análisis de Outliers / Anomalías")

    sensor_cols = [c for c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion'] if c in df.columns]
    if not sensor_cols:
        return

    method = st.radio("Criterio de Umbral", ["IQR (1.5x Rango Intercuartílico)", "IQR (3.0x Extremo)", "Z-Score (|Z| > 3.0)"], horizontal=True)

    outlier_results = {}
    for sensor in sensor_cols:
        data = df[sensor].dropna()
        if data.empty:
            continue

        if "1.5x" in method:
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        elif "3.0x" in method:
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 3.0 * IQR, Q3 + 3.0 * IQR
        else:
            z_scores = np.abs(stats.zscore(data))
            lower, upper = data[z_scores <= 3].min(), data[z_scores <= 3].max()

        outliers = data[(data < lower) | (data > upper)]
        outlier_results[sensor] = {
            'count': len(outliers),
            'percentage': (len(outliers) / len(data) * 100) if len(data) > 0 else 0,
            'lower': lower,
            'upper': upper,
            'values': outliers
        }

    summary_df = pd.DataFrame({
        'Sensor': list(outlier_results.keys()),
        'Anomalías Detectadas': [r['count'] for r in outlier_results.values()],
        'Porcentaje (%)': [f"{r['percentage']:.2f}%" for r in outlier_results.values()],
        'Umbral Inferior': [f"{r['lower']:.2f}" for r in outlier_results.values()],
        'Umbral Superior': [f"{r['upper']:.2f}" for r in outlier_results.values()]
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


def render_filtered_data(df: pd.DataFrame):
    """Render filtered data table with CSV export"""
    st.markdown("### 📋 Vista de Datos Crudos Procesados")
    paginated_dataframe(df, key="eda_data")

    from ui.components import download_button
    download_button(df, "telemetria_eda_unt.csv", "📥 Descargar Muestra Filtrada (CSV)")
