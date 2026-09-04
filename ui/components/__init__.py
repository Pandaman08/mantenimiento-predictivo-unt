import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)
from utils.helpers import sanitize_text

# UNT Theme Palette
UNT_PRIMARY = "#0A2B5E"
UNT_PRIMARY_LIGHT = "#123F80"
UNT_GOLD = "#C5A55A"
UNT_GOLD_LIGHT = "#DFC382"
UNT_SUCCESS = "#059669"
UNT_WARNING = "#D97706"
UNT_DANGER = "#DC2626"
UNT_INFO = "#0284C7"
UNT_TEXT = "#0F172A"
UNT_MUTED = "#475569"
UNT_CARD_BG = "#FFFFFF"

def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """Apply unified UNT industrial palette and layout to Plotly figures"""
    fig.update_layout(
        font=dict(family="Inter, sans-serif", color=UNT_TEXT),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            tickfont=dict(color=UNT_MUTED, size=11),
            titlefont=dict(color=UNT_TEXT, size=12, family="Inter, sans-serif")
        ),
        yaxis=dict(
            gridcolor="#E2E8F0",
            zerolinecolor="#CBD5E1",
            tickfont=dict(color=UNT_MUTED, size=11),
            titlefont=dict(color=UNT_TEXT, size=12, family="Inter, sans-serif")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=UNT_MUTED)
        ),
        hoverlabel=dict(
            bgcolor=UNT_PRIMARY,
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#FFFFFF"
        )
    )
    return fig

def show_loading(message: str = "Cargando datos..."):
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

def render_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_positive: bool = True,
    icon: str = "📊",
    subtitle: Optional[str] = None
):
    """Render modern industrial KPI card"""
    # sanitize dynamic content to avoid HTML/script injection
    title_safe = sanitize_text(title)
    value_safe = sanitize_text(value)
    subtitle_safe = sanitize_text(subtitle) if subtitle else ''

    delta_html = ""
    if delta:
        delta_color = UNT_SUCCESS if delta_positive else UNT_DANGER
        delta_arrow = "▲" if delta_positive else "▼"
        delta_html = f"""
            <span style="font-size:0.8rem; font-weight:700; color:{delta_color}; margin-left:6px;">
                {delta_arrow} {sanitize_text(delta)}
            </span>
        """

    sub_html = f"<div style='font-size:0.75rem; color:{UNT_MUTED}; margin-top:4px;'>{subtitle_safe}</div>" if subtitle else ""

    st.html(
        f"""
        <div class="unt-kpi-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
                <span style="font-size:0.82rem; font-weight:600; color:{UNT_MUTED}; text-transform:uppercase; letter-spacing:0.04em;">
                    {title_safe}
                </span>
                <span class="unt-kpi-icon">{icon}</span>
            </div>
            <div style="display:flex; align-items:baseline; gap:0.3rem;">
                <span style="font-size:1.85rem; font-weight:800; color:{UNT_PRIMARY}; letter-spacing:-0.02em;">
                    {value_safe}
                </span>
                {delta_html}
            </div>
            {sub_html}
        </div>
        """
    )

def create_kpi_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Backward compatible KPI card wrapper"""
    is_positive = True
    if delta:
        if delta_color == "inverse":
            is_positive = not delta.startswith("+")
        else:
            is_positive = not delta.startswith("-")
    render_metric_card(title, value, delta=delta, delta_positive=is_positive)

def render_equipment_health_card(
    codigo: str,
    nombre: str,
    tipo: str,
    estado: str,
    health_score: float,
    temp: Optional[float] = None,
    vib: Optional[float] = None,
    pres: Optional[float] = None,
    hours: Optional[float] = None
):
    """Render equipment health status card"""
    # Color badge according to health score
    if health_score >= 80:
        health_color = UNT_SUCCESS
        health_label = "Óptimo"
        badge_class = "status-pill-success"
    elif health_score >= 50:
        health_color = UNT_WARNING
        health_label = "Atención"
        badge_class = "status-pill-warning"
    else:
        health_color = UNT_DANGER
        health_label = "Crítico"
        badge_class = "status-pill-danger"

    icon_map = {
        "pala": "⛏️",
        "camion": "🚚",
        "perforadora": "🔩",
    }
    icon = icon_map.get(tipo.lower(), "🚜")

    # sanitize identifiers and names to avoid injection in templates
    codigo_safe = sanitize_text(codigo)
    nombre_safe = sanitize_text(nombre)

    temp_str = f"{temp:.1f}°C" if temp is not None else "--"
    vib_str = f"{vib:.2f} mm/s" if vib is not None else "--"
    pres_str = f"{pres:.0f} PSI" if pres is not None else "--"
    hours_str = f"{hours:,.0f}h" if hours is not None else "--"

    st.html(
        f"""
        <div class="unt-machine-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:1.4rem;">{icon}</span>
                    <div>
                        <div style="font-weight:700; font-size:1.05rem; color:{UNT_PRIMARY};">{codigo_safe}</div>
                        <div style="font-size:0.75rem; color:{UNT_MUTED};">{nombre_safe}</div>
                    </div>
                </div>
                <span class="{badge_class}">{health_label}</span>
            </div>

            <div style="margin:10px 0;">
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:600; color:{UNT_MUTED}; margin-bottom:4px;">
                    <span>Índice de Salud</span>
                    <span style="color:{health_color}; font-weight:800;">{health_score:.1f}%</span>
                </div>
                <div style="background:#E2E8F0; border-radius:999px; height:8px; overflow:hidden;">
                    <div style="background:{health_color}; width:{max(min(health_score, 100), 5)}%; height:100%; border-radius:999px;"></div>
                </div>
            </div>

            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; background:#F8FAFC; padding:8px; border-radius:10px; border:1px solid #E2E8F0; font-size:0.75rem; margin-top:8px;">
                <div>
                    <span style="color:{UNT_MUTED}; display:block;">Temp</span>
                    <strong style="color:{UNT_TEXT};">{temp_str}</strong>
                </div>
                <div>
                    <span style="color:{UNT_MUTED}; display:block;">Vibración</span>
                    <strong style="color:{UNT_TEXT};">{vib_str}</strong>
                </div>
                <div>
                    <span style="color:{UNT_MUTED}; display:block;">Presión</span>
                    <strong style="color:{UNT_TEXT};">{pres_str}</strong>
                </div>
            </div>
        </div>
        """
    )

def plot_gauge_chart(
    value: float,
    title: str = "Probabilidad de Falla",
    threshold_warning: float = 40.0,
    threshold_danger: float = 75.0,
    height: int = 240
) -> go.Figure:
    """Create industrial gauge chart for failure probability"""
    bar_color = UNT_SUCCESS
    if value >= threshold_danger:
        bar_color = UNT_DANGER
    elif value >= threshold_warning:
        bar_color = UNT_WARNING

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14, 'color': UNT_TEXT, 'family': 'Inter'}},
        number={'suffix': "%", 'font': {'size': 26, 'color': bar_color, 'family': 'Inter', 'weight': 'bold'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': UNT_MUTED, 'tickfont': {'size': 10}},
            'bar': {'color': bar_color, 'thickness': 0.28},
            'bgcolor': "#FFFFFF",
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, threshold_warning], 'color': "rgba(16, 185, 129, 0.12)"},
                {'range': [threshold_warning, threshold_danger], 'color': "rgba(245, 158, 11, 0.14)"},
                {'range': [threshold_danger, 100], 'color': "rgba(239, 68, 68, 0.18)"}
            ],
            'threshold': {
                'line': {'color': UNT_DANGER, 'width': 3},
                'thickness': 0.75,
                'value': threshold_danger
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=15, t=35, b=10),
        height=height
    )
    return fig

def plot_time_series(df: pd.DataFrame, x: str, y: str, color: str = None,
                     title: str = "", height: int = 400) -> go.Figure:
    """Create interactive time series plot styled with UNT theme"""
    fig = px.line(
        df, x=x, y=y, color=color, title=title, height=height,
        color_discrete_sequence=[UNT_PRIMARY, UNT_GOLD, UNT_INFO, UNT_WARNING, UNT_SUCCESS]
    )
    fig.update_layout(
        xaxis_title="Fecha y Hora",
        yaxis_title=y.replace("_", " ").title(),
        hovermode='x unified'
    )
    return apply_plotly_theme(fig)

def plot_histogram(df: pd.DataFrame, x: str, color: str = None,
                   title: str = "", bins: int = 30, height: int = 400) -> go.Figure:
    """Create styled histogram"""
    fig = px.histogram(
        df, x=x, color=color, title=title, nbins=bins, height=height,
        marginal="box", opacity=0.8,
        color_discrete_sequence=[UNT_PRIMARY, UNT_GOLD, UNT_INFO, UNT_DANGER]
    )
    return apply_plotly_theme(fig)

def plot_boxplot(df: pd.DataFrame, x: str, y: str, color: str = None,
                 title: str = "", height: int = 400) -> go.Figure:
    """Create styled box plot"""
    fig = px.box(
        df, x=x, y=y, color=color, title=title, height=height,
        color_discrete_sequence=[UNT_PRIMARY, UNT_GOLD, UNT_INFO, UNT_DANGER]
    )
    return apply_plotly_theme(fig)

def plot_correlation_heatmap(df: pd.DataFrame, title: str = "Matriz de Correlación",
                             height: int = 480) -> go.Figure:
    """Create correlation heatmap with UNT palette"""
    numeric_df = df.select_dtypes(include=['number'])
    corr = numeric_df.corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale=[
            [0.0, "#0A2B5E"],
            [0.5, "#FFFFFF"],
            [1.0, "#C5A55A"]
        ],
        zmid=0,
        text=corr.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 11, "family": "Inter"},
        hoverongaps=False
    ))
    fig.update_layout(title=title, height=height)
    return apply_plotly_theme(fig)

def plot_scatter_matrix(df: pd.DataFrame, dimensions: List[str], color: str = None,
                        title: str = "Matriz de Dispersión", height: int = 580) -> go.Figure:
    """Create scatter plot matrix"""
    fig = px.scatter_matrix(
        df, dimensions=dimensions, color=color, title=title, height=height,
        color_discrete_sequence=[UNT_PRIMARY, UNT_GOLD, UNT_INFO]
    )
    return apply_plotly_theme(fig)

def paginated_dataframe(df: pd.DataFrame, page_size: int = 25, key: str = "df") -> pd.DataFrame:
    """Display paginated dataframe with clean controls"""
    if df.empty:
        st.info("No hay datos disponibles para mostrar")
        return df

    total_pages = max(1, (len(df) - 1) // page_size + 1)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, key=f"{key}_page")
    with c2:
        st.html(
            f"""
            <div style='padding-top:28px; font-size:0.85rem; color:{UNT_MUTED}; text-align:center;'>
                Mostrando {(page-1)*page_size + 1} - {min(page*page_size, len(df))} de {len(df):,} registros
            </div>
            """
        )
    with c3:
        page_size = st.selectbox("Filas por pág.", [15, 25, 50, 100], index=1, key=f"{key}_pagesize")

    start = (page - 1) * page_size
    end = start + page_size

    sliced = df.iloc[start:end]
    st.dataframe(sliced, use_container_width=True, hide_index=True)
    return sliced

def filter_dataframe_ui(df: pd.DataFrame, key: str = "filter") -> pd.DataFrame:
    """UI for filtering dataframe"""
    if df.empty:
        return df

    with st.expander("🔍 Filtros de Búsqueda y Filtrado", expanded=False):
        filtered_df = df.copy()

        # Date range filter
        date_cols = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns
        if len(date_cols) > 0:
            date_col = st.selectbox("Columna temporal", date_cols, key=f"{key}_date_col")
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_date.date() if hasattr(min_date, 'date') else min_date,
                       max_date.date() if hasattr(max_date, 'date') else max_date),
                key=f"{key}_date_range"
            )
            if len(date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df[date_col] >= pd.Timestamp(date_range[0])) &
                    (filtered_df[date_col] <= pd.Timestamp(date_range[1]))
                ]

        # Categorical filters
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            cols_ui = st.columns(min(len(cat_cols), 3))
            for i, col in enumerate(cat_cols[:3]):
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) < 40:
                    with cols_ui[i % 3]:
                        selected = st.multiselect(f"Filtrar {col}", unique_vals, key=f"{key}_{col}")
                        if selected:
                            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    return filtered_df

def download_button(df: pd.DataFrame, filename: str, label: str = "📥 Descargar CSV"):
    """Create download button for dataframe"""
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label, csv, file_name=filename, mime='text/csv', use_container_width=True)

def plot_confusion_matrix(cm: list, labels: List[str] = None, title: str = "Matriz de Confusión") -> go.Figure:
    """Plot confusion matrix as heatmap with UNT palette"""
    if labels is None:
        labels = ['No Falla (Normal)', 'Falla Inminente']

    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=[f'Pred: {l}' for l in labels],
        y=[f'Real: {l}' for l in labels],
        colorscale=[
            [0.0, "#F1F5F9"],
            [0.5, "#93C5FD"],
            [1.0, "#0A2B5E"]
        ],
        text=cm,
        texttemplate='<b>%{text}</b>',
        textfont={"size": 18, "family": "Inter"},
        hoverongaps=False
    ))
    fig.update_layout(title=title, height=380)
    return apply_plotly_theme(fig)

def plot_roc_curve(fpr: dict, tpr: dict, auc_scores: dict, title: str = "Curvas ROC Comparativas") -> go.Figure:
    """Plot ROC curves for multiple models with UNT palette"""
    fig = go.Figure()
    palette = [UNT_PRIMARY, UNT_GOLD, UNT_INFO, UNT_SUCCESS, UNT_DANGER]

    for i, model_name in enumerate(fpr):
        color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=fpr[model_name], y=tpr[model_name],
            mode='lines', name=f"{model_name} (AUC={auc_scores.get(model_name, 0):.3f})",
            line=dict(color=color, width=2.5)
        ))

    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(dash='dash', color='#94A3B8', width=1.5),
        name='Referencia Aleatoria'
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Tasa de Falsos Positivos (1 - Especificidad)',
        yaxis_title='Tasa de Verdaderos Positivos (Sensibilidad)',
        height=450
    )
    return apply_plotly_theme(fig)

def plot_learning_curve(train_sizes: list, train_scores: list, val_scores: list,
                        title: str = "Curva de Aprendizaje") -> go.Figure:
    """Plot learning curve"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=train_sizes, y=train_scores,
        mode='lines+markers', name='Entrenamiento',
        line=dict(color=UNT_PRIMARY, width=2.5)
    ))

    fig.add_trace(go.Scatter(
        x=train_sizes, y=val_scores,
        mode='lines+markers', name='Validación',
        line=dict(color=UNT_GOLD, width=2.5)
    ))

    fig.update_layout(
        title=title,
        xaxis_title='Tamaño del conjunto de entrenamiento',
        yaxis_title='F1-Score / Rendimiento',
        height=380
    )
    return apply_plotly_theme(fig)

def render_business_objectives():
    """Render business objectives section (CRISP-DM Phase 1)"""
    from config.settings import settings

    objectives = settings.BUSINESS_OBJECTIVES
    col1, col2, col3 = st.columns(3)

    with col1:
        render_metric_card(
            "Reducción MTTR",
            f"-{objectives.get('reduce_mttr_percent', 20)}%",
            delta="-3.5h",
            delta_positive=True,
            icon="⏱️",
            subtitle="Tiempo medio de reparación"
        )
    with col2:
        render_metric_card(
            "Aumento Disponibilidad",
            f"+{objectives.get('increase_availability_percent', 5)}%",
            delta="+2.1%",
            delta_positive=True,
            icon="📈",
            subtitle="Disponibilidad global de flota"
        )
    with col3:
        render_metric_card(
            "Ahorro de Mantenimiento",
            f"-{objectives.get('reduce_maintenance_cost_percent', 15)}%",
            delta="S/ 96,000",
            delta_positive=True,
            icon="💰",
            subtitle="Costos correctivos evitados"
        )

def render_crisp_dm_phase_indicator(current_phase: int):
    """Render modern responsive CRISP-DM phase stepper"""
    phases = [
        ("1", "🎯 Negocio", "01_Business_Understanding"),
        ("2", "📈 Datos EDA", "eda"),
        ("3", "🧹 Preparación", "03_Data_Preparation"),
        ("4", "🤖 Modelado", "training"),
        ("5", "📊 Evaluación", "evaluation"),
        ("6", "🚀 Despliegue", "prediction")
    ]

    st.html(
        f"""
        <div class="unt-stepper-container">
            <div style="font-size:0.75rem; text-transform:uppercase; font-weight:700; color:{UNT_GOLD}; letter-spacing:0.08em; margin-bottom:8px;">
                Metodología Minería de Datos & CRISP-DM
            </div>
        </div>
        """
    )

    cols = st.columns(6)
    for i, (num, name, page_key) in enumerate(phases):
        phase_num = i + 1
        with cols[i]:
            if phase_num == current_phase:
                state_class = "step-item active"
                badge = f"FASE {num} · ACTIVA"
            elif phase_num < current_phase:
                state_class = "step-item completed"
                badge = f"✓ FASE {num} · LISTA"
            else:
                state_class = "step-item upcoming"
                badge = f"FASE {num}"

            st.html(
                f"""
                <div class="{state_class}">
                    <div class="step-badge">{badge}</div>
                    <div class="step-title">{name}</div>
                </div>
                """
            )

    st.markdown("", unsafe_allow_html=True)
