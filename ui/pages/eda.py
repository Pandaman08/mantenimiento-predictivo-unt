import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from src.db.connection import db_pool
from ui.components import (plot_histogram, plot_boxplot, plot_correlation_heatmap, 
                          plot_scatter_matrix, filter_dataframe_ui, paginated_dataframe,
                          render_crisp_dm_phase_indicator, show_loading)

def render_eda():
    render_crisp_dm_phase_indicator(2)
    
    st.markdown("## 📈 Análisis Exploratorio de Datos (EDA) - Fase 2 CRISP-DM")
    
    # Load data
    with show_loading("Cargando datos para EDA..."):
        df = load_eda_data()
    
    if df.empty:
        st.warning("No hay datos disponibles. Ejecute la generación de datos sintéticos primero.")
        if st.button("🔄 Generar Datos Sintéticos"):
            st.info("Ejecute: python generate_data.py")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filtros EDA")
        equipo_filter = st.selectbox("Equipo", ["Todos"] + df['equipo_codigo'].unique().tolist())
        sensor_types = st.multiselect("Sensores", df['tipo_sensor'].unique().tolist(), 
                                     default=df['tipo_sensor'].unique().tolist())
        date_range = st.date_input("Rango de fechas", 
                                  value=(df['timestamp'].min().date(), df['timestamp'].max().date()))
    
    # Apply filters
    filtered_df = df.copy()
    if equipo_filter != "Todos":
        filtered_df = filtered_df[filtered_df['equipo_codigo'] == equipo_filter]
    if sensor_types:
        filtered_df = filtered_df[filtered_df['tipo_sensor'].isin(sensor_types)]
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['timestamp'].dt.date >= date_range[0]) & 
            (filtered_df['timestamp'].dt.date <= date_range[1])
        ]
    
    st.info(f"Registros filtrados: {len(filtered_df):,} de {len(df):,}")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Estadísticas Descriptivas", 
        "📈 Distribuciones", 
        "🔗 Correlaciones", 
        "🎯 Outliers", 
        "📋 Datos Filtrados"
    ])
    
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
        
        return df_pivot
    except Exception as e:
        st.error(f"Error cargando datos EDA: {e}")
        return pd.DataFrame()

def render_descriptive_stats(df: pd.DataFrame):
    """Render descriptive statistics"""
    st.markdown("### 📊 Estadísticas Descriptivas")
    
    sensor_cols = [c for c in df.columns if c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']]
    
    if not sensor_cols:
        st.warning("No hay columnas de sensores en los datos")
        return
    
    # Overall stats
    stats_df = df[sensor_cols].describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T
    stats_df = stats_df.round(3)
    st.dataframe(stats_df, use_container_width=True)
    
    # By equipment type
    st.markdown("#### Por Tipo de Equipo")
    if 'equipo_tipo' in df.columns:
        for eq_type in df['equipo_tipo'].unique():
            with st.expander(f"{eq_type.capitalize()}"):
                eq_df = df[df['equipo_tipo'] == eq_type][sensor_cols]
                if not eq_df.empty:
                    st.dataframe(eq_df.describe().T.round(3), use_container_width=True)

def render_distributions(df: pd.DataFrame):
    """Render distribution plots"""
    st.markdown("### 📈 Distribuciones de Variables")
    
    sensor_cols = [c for c in df.columns if c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histograms
        selected_sensor = st.selectbox("Sensor para histograma", sensor_cols)
        fig = plot_histogram(df, selected_sensor, color='equipo_tipo' if 'equipo_tipo' in df.columns else None,
                            title=f"Distribución de {selected_sensor.capitalize()}")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Boxplots
        fig = plot_boxplot(df, 'equipo_tipo' if 'equipo_tipo' in df.columns else 'equipo_codigo', 
                          selected_sensor, title=f"{selected_sensor.capitalize()} por Equipo")
        st.plotly_chart(fig, use_container_width=True)
    
    # All sensors boxplot
    st.markdown("#### Boxplots de Todos los Sensores")
    melted = df[sensor_cols + ['equipo_tipo']].melt(id_vars=['equipo_tipo'], var_name='Sensor', value_name='Valor')
    fig = px.box(melted, x='Sensor', y='Valor', color='equipo_tipo', height=500)
    fig.update_layout(template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)
    
    # Q-Q plots for normality
    st.markdown("#### Q-Q Plots (Normalidad)")
    qq_cols = st.columns(len(sensor_cols))
    for i, sensor in enumerate(sensor_cols):
        with qq_cols[i]:
            data = df[sensor].dropna()
            if len(data) > 3:
                theoretical_quantiles = stats.norm.ppf((np.arange(len(data)) + 0.5) / len(data))
                sample_quantiles = np.sort(data)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=theoretical_quantiles, y=sample_quantiles, mode='markers', name=sensor))
                fig.add_trace(go.Scatter(x=[theoretical_quantiles.min(), theoretical_quantiles.max()], 
                                        y=[theoretical_quantiles.min(), theoretical_quantiles.max()], 
                                        mode='lines', line=dict(dash='dash', color='red'), name='Normal'))
                fig.update_layout(title=sensor.capitalize(), height=300, template='plotly_white',
                                 xaxis_title="Cuantiles Teóricos", yaxis_title="Cuantiles Muestrales")
                st.plotly_chart(fig, use_container_width=True)

def render_correlations(df: pd.DataFrame):
    """Render correlation analysis"""
    st.markdown("### 🔗 Análisis de Correlación")
    
    sensor_cols = [c for c in df.columns if c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']]
    
    # Heatmap
    fig = plot_correlation_heatmap(df[sensor_cols], "Matriz de Correlación - Todos los Equipos")
    st.plotly_chart(fig, use_container_width=True)
    
    # By equipment type
    if 'equipo_tipo' in df.columns:
        st.markdown("#### Correlación por Tipo de Equipo")
        eq_types = df['equipo_tipo'].unique()
        cols = st.columns(len(eq_types))
        for i, eq_type in enumerate(eq_types):
            with cols[i]:
                eq_df = df[df['equipo_tipo'] == eq_type][sensor_cols]
                if not eq_df.empty:
                    fig = plot_correlation_heatmap(eq_df, f"{eq_type.capitalize()}", height=350)
                    st.plotly_chart(fig, use_container_width=True)
    
    # Scatter matrix
    st.markdown("#### Matriz de Dispersión")
    if st.checkbox("Mostrar matriz de dispersión (puede ser lento con muchos datos)"):
        sample_df = df[sensor_cols].sample(min(1000, len(df)))
        fig = plot_scatter_matrix(sample_df, sensor_cols, color=df.loc[sample_df.index, 'equipo_tipo'] if 'equipo_tipo' in df.columns else None)
        st.plotly_chart(fig, use_container_width=True)

def render_outliers(df: pd.DataFrame):
    """Render outlier detection"""
    st.markdown("### 🎯 Detección de Outliers")
    
    sensor_cols = [c for c in df.columns if c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']]
    
    method = st.radio("Método", ["IQR (1.5x)", "IQR (3x)", "Z-Score (3σ)"], horizontal=True)
    
    outlier_results = {}
    
    for sensor in sensor_cols:
        data = df[sensor].dropna()
        
        if method == "IQR (1.5x)":
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
        elif method == "IQR (3x)":
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 3 * IQR, Q3 + 3 * IQR
        else:  # Z-Score
            z_scores = np.abs(stats.zscore(data))
            lower, upper = data[z_scores <= 3].min(), data[z_scores <= 3].max()
        
        outliers = data[(data < lower) | (data > upper)]
        outlier_results[sensor] = {
            'count': len(outliers),
            'percentage': len(outliers) / len(data) * 100,
            'lower': lower,
            'upper': upper,
            'values': outliers
        }
    
    # Summary table
    summary_df = pd.DataFrame({
        'Sensor': list(outlier_results.keys()),
        'Outliers': [r['count'] for r in outlier_results.values()],
        'Porcentaje': [f"{r['percentage']:.2f}%" for r in outlier_results.values()],
        'Límite Inferior': [f"{r['lower']:.2f}" for r in outlier_results.values()],
        'Límite Superior': [f"{r['upper']:.2f}" for r in outlier_results.values()]
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Visualize outliers
    selected_sensor = st.selectbox("Visualizar outliers de:", sensor_cols)
    result = outlier_results[selected_sensor]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=df[selected_sensor].dropna(), name='Todos', opacity=0.7, nbinsx=50))
    if len(result['values']) > 0:
        fig.add_trace(go.Histogram(x=result['values'], name='Outliers', opacity=0.7, nbinsx=50, marker_color='red'))
    fig.add_vline(x=result['lower'], line_dash="dash", line_color="red", annotation_text="Límite Inf.")
    fig.add_vline(x=result['upper'], line_dash="dash", line_color="red", annotation_text="Límite Sup.")
    fig.update_layout(title=f"Outliers en {selected_sensor.capitalize()} ({method})", 
                     template='plotly_white', barmode='overlay')
    st.plotly_chart(fig, use_container_width=True)
    
    # Show outlier values
    if len(result['values']) > 0:
        with st.expander(f"Ver {len(result['values'])} valores atípicos"):
            st.dataframe(result['values'].reset_index(drop=True), use_container_width=True)

def render_filtered_data(df: pd.DataFrame):
    """Render filtered data table"""
    st.markdown("### 📋 Datos Filtrados")
    
    # Show basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Registros", f"{len(df):,}")
    with col2:
        st.metric("Equipos", df['equipo_codigo'].nunique() if 'equipo_codigo' in df.columns else 0)
    with col3:
        st.metric("Sensores", len([c for c in df.columns if c in ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion']]))
    
    # Paginated table
    paginated_dataframe(df, key="eda_data")
    
    # Download
    from ui.components import download_button
    download_button(df, "eda_filtered_data.csv", "📥 Descargar datos filtrados (CSV)")