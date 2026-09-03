import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

def show_loading(message: str = "Cargando..."):
    """Show loading spinner"""
    return st.spinner(message)

def show_error(message: str):
    """Show error message"""
    st.error(f"❌ {message}")

def show_success(message: str):
    """Show success message"""
    st.success(f"✅ {message}")

def show_warning(message: str):
    """Show warning message"""
    st.warning(f"⚠️ {message}")

def show_info(message: str):
    """Show info message"""
    st.info(f"ℹ️ {message}")

def format_number(num: float, decimals: int = 2) -> str:
    """Format number with thousands separator"""
    if num >= 1e6:
        return f"{num/1e6:.{decimals}f}M"
    elif num >= 1e3:
        return f"{num/1e3:.{decimals}f}K"
    return f"{num:.{decimals}f}"

def create_kpi_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Create a KPI metric card"""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)

def plot_time_series(df: pd.DataFrame, x: str, y: str, color: str = None,
                     title: str = "", height: int = 400) -> go.Figure:
    """Create interactive time series plot"""
    fig = px.line(df, x=x, y=y, color=color, title=title, height=height)
    fig.update_layout(
        xaxis_title="Fecha/Hora",
        yaxis_title=y,
        hovermode='x unified',
        template='plotly_white'
    )
    return fig

def plot_histogram(df: pd.DataFrame, x: str, color: str = None,
                   title: str = "", bins: int = 30, height: int = 400) -> go.Figure:
    """Create histogram"""
    fig = px.histogram(df, x=x, color=color, title=title, nbins=bins, height=height,
                       marginal="box", opacity=0.7)
    fig.update_layout(template='plotly_white')
    return fig

def plot_boxplot(df: pd.DataFrame, x: str, y: str, color: str = None,
                 title: str = "", height: int = 400) -> go.Figure:
    """Create box plot"""
    fig = px.box(df, x=x, y=y, color=color, title=title, height=height)
    fig.update_layout(template='plotly_white')
    return fig

def plot_correlation_heatmap(df: pd.DataFrame, title: str = "Matriz de Correlación",
                             height: int = 500) -> go.Figure:
    """Create correlation heatmap"""
    numeric_df = df.select_dtypes(include=['number'])
    corr = numeric_df.corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False
    ))
    fig.update_layout(title=title, height=height, template='plotly_white')
    return fig

def plot_scatter_matrix(df: pd.DataFrame, dimensions: List[str], color: str = None,
                        title: str = "Matriz de Dispersión", height: int = 600) -> go.Figure:
    """Create scatter plot matrix"""
    fig = px.scatter_matrix(df, dimensions=dimensions, color=color, title=title, height=height)
    fig.update_layout(template='plotly_white')
    return fig

def paginated_dataframe(df: pd.DataFrame, page_size: int = 50, key: str = "df") -> pd.DataFrame:
    """Display paginated dataframe with controls"""
    if df.empty:
        st.info("No hay datos para mostrar")
        return df

    total_pages = (len(df) - 1) // page_size + 1

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, key=f"{key}_page")
    with col2:
        st.write(f"Mostrando {(page-1)*page_size + 1} - {min(page*page_size, len(df))} de {len(df)} registros")
    with col3:
        page_size = st.selectbox("Por página", [25, 50, 100, 200], index=1, key=f"{key}_pagesize")

    start = (page - 1) * page_size
    end = start + page_size

    return df.iloc[start:end]

def filter_dataframe_ui(df: pd.DataFrame, key: str = "filter") -> pd.DataFrame:
    """UI for filtering dataframe"""
    if df.empty:
        return df

    with st.expander("🔍 Filtros", expanded=False):
        filtered_df = df.copy()

        # Date range filter
        date_cols = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        if len(date_cols) > 0:
            date_col = st.selectbox("Columna de fecha", date_cols, key=f"{key}_date_col")
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key=f"{key}_date_range"
            )
            if len(date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df[date_col] >= pd.Timestamp(date_range[0])) &
                    (filtered_df[date_col] <= pd.Timestamp(date_range[1]))
                ]

        # Categorical filters
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols[:5]:  # Limit to 5 categorical filters
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) < 50:
                selected = st.multiselect(f"Filtrar por {col}", unique_vals, key=f"{key}_{col}")
                if selected:
                    filtered_df = filtered_df[filtered_df[col].isin(selected)]

        # Numeric range filters
        num_cols = df.select_dtypes(include=['number']).columns
        for col in num_cols[:5]:  # Limit to 5 numeric filters
            min_val, max_val = float(df[col].min()), float(df[col].max())
            if min_val != max_val:
                range_vals = st.slider(
                    f"Rango {col}",
                    min_val, max_val,
                    (min_val, max_val),
                    key=f"{key}_{col}_range"
                )
                filtered_df = filtered_df[
                    (filtered_df[col] >= range_vals[0]) &
                    (filtered_df[col] <= range_vals[1])
                ]

    return filtered_df

def download_button(df: pd.DataFrame, filename: str, label: str = "📥 Descargar CSV"):
    """Create download button for dataframe"""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label, csv, file_name=filename, mime='text/csv')

def plot_confusion_matrix(cm: list, labels: List[str] = None, title: str = "Matriz de Confusión") -> go.Figure:
    """Plot confusion matrix as heatmap"""
    if labels is None:
        labels = ['No Falla', 'Falla']

    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=[f'Pred: {l}' for l in labels],
        y=[f'Real: {l}' for l in labels],
        colorscale='Blues',
        text=cm,
        texttemplate='%{text}',
        textfont={"size": 16}
    ))
    fig.update_layout(title=title, template='plotly_white', height=400)
    return fig

def plot_roc_curve(fpr: dict, tpr: dict, auc_scores: dict, title: str = "Curvas ROC") -> go.Figure:
    """Plot ROC curves for multiple models"""
    fig = go.Figure()

    for model_name in fpr:
        fig.add_trace(go.Scatter(
            x=fpr[model_name], y=tpr[model_name],
            mode='lines', name=f"{model_name} (AUC={auc_scores[model_name]:.3f})"
        ))

    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(dash='dash', color='gray'), name='Aleatorio'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Tasa de Falsos Positivos',
        yaxis_title='Tasa de Verdaderos Positivos',
        template='plotly_white',
        height=500
    )
    return fig

def plot_learning_curve(train_sizes: list, train_scores: list, val_scores: list,
                        title: str = "Curva de Aprendizaje") -> go.Figure:
    """Plot learning curve"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=train_sizes, y=train_scores,
        mode='lines+markers', name='Entrenamiento',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=train_sizes, y=val_scores,
        mode='lines+markers', name='Validación',
        line=dict(color='red')
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Tamaño del conjunto de entrenamiento',
        yaxis_title='Score',
        template='plotly_white',
        height=400
    )
    return fig

def render_business_objectives():
    """Render business objectives section (CRISP-DM Phase 1)"""
    from config.settings import settings

    st.markdown("## 🎯 Objetivos de Negocio (Fase 1 CRISP-DM)")

    col1, col2, col3 = st.columns(3)

    objectives = settings.BUSINESS_OBJECTIVES
    with col1:
        st.metric("Reducir MTTR", f"{objectives['reduce_mttr_percent']}%", "Objetivo")
    with col2:
        st.metric("Aumentar Disponibilidad", f"{objectives['increase_availability_percent']}%", "Objetivo")
    with col3:
        st.metric("Reducir Costos Mantenimiento", f"{objectives['reduce_maintenance_cost_percent']}%", "Objetivo")

    st.markdown("### 📊 Criterios de Éxito del Modelo")
    criteria = settings.MODEL_SUCCESS_CRITERIA

    cols = st.columns(4)
    for i, (metric, target) in enumerate(criteria.items()):
        with cols[i]:
            st.metric(metric.replace('_', ' ').title(), f"{target:.2%}" if isinstance(target, float) else f"{target}s")

def render_crisp_dm_phase_indicator(current_phase: int):
    """Render CRISP-DM phase indicator"""
    phases = [
        ("1", "Comprensión del Negocio"),
        ("2", "Comprensión de los Datos"),
        ("3", "Preparación de los Datos"),
        ("4", "Modelado"),
        ("5", "Evaluación"),
        ("6", "Despliegue")
    ]

    cols = st.columns(6)
    for i, (num, name) in enumerate(phases):
        with cols[i]:
            if i + 1 == current_phase:
                st.markdown(f"""
                <div style="background: #2a5298; color: white; padding: 0.5rem;
                            border-radius: 8px; text-align: center;">
                    <strong>Fase {num}</strong><br>
                    <small>{name}</small>
                </div>
                """, unsafe_allow_html=True)
            elif i + 1 < current_phase:
                st.markdown(f"""
                <div style="background: #44aa44; color: white; padding: 0.5rem;
                            border-radius: 8px; text-align: center;">
                    <strong>✓ Fase {num}</strong><br>
                    <small>{name}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f0f2f6; color: #666; padding: 0.5rem;
                            border-radius: 8px; text-align: center;">
                    <strong>Fase {num}</strong><br>
                    <small>{name}</small>
                </div>
                """, unsafe_allow_html=True)