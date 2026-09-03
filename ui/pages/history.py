import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.db.connection import db_pool
from ui.components import filter_dataframe_ui, paginated_dataframe, show_loading

def render_history():
    st.markdown("## 📋 Historial de Predicciones")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        days_back = st.selectbox("Período", [1, 7, 30, 90, 365], index=2, format_func=lambda x: f"Últimos {x} días")
    with col2:
        equipo_filter = st.selectbox("Equipo", ["Todos"] + get_equipos_list())
    with col3:
        model_filter = st.selectbox("Modelo", ["Todos"] + get_models_list())
    with col4:
        status_filter = st.selectbox("Estado", ["Todas", "Falla Predicha", "Normal", "Confirmada", "Falso Positivo"])
    
    # Load data
    with show_loading("Cargando historial..."):
        df = load_predictions_history(days_back, equipo_filter, model_filter, status_filter)
    
    if df.empty:
        show_info("No hay predicciones en el período seleccionado")
        return
    
    # Summary metrics
    st.markdown("### 📊 Resumen")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("Total Predicciones", len(df))
    with mcol2:
        fallas = df['falla_predicha'].sum()
        st.metric("Fallas Predichas", int(fallas))
    with mcol3:
        if len(df) > 0:
            st.metric("Tasa Fallas", f"{fallas/len(df)*100:.1f}%")
    with mcol4:
        avg_conf = df['confianza'].mean()
        st.metric("Confianza Promedio", f"{avg_conf:.1%}")
    
    # Charts
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Predictions over time
        daily = df.set_index('timestamp_prediccion').resample('D')['falla_predicha'].sum().reset_index()
        fig = px.line(daily, x='timestamp_prediccion', y='falla_predicha', 
                     title="Predicciones de Falla por Día")
        fig.update_layout(template='plotly_white', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        # Confidence distribution
        fig = px.histogram(df, x='confianza', color='falla_predicha', 
                          title="Distribución de Confianza", nbins=30,
                          labels={'falla_predicha': 'Falla Predicha'})
        fig.update_layout(template='plotly_white', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Accuracy tracking (if real failures known)
    confirmed = df[df['timestamp_real_falla'].notna()]
    if len(confirmed) > 0:
        st.markdown("### ✅ Validación de Predicciones")
        tp = len(confirmed[(confirmed['falla_predicha'] == True) & (confirmed['timestamp_real_falla'].notna())])
        fp = len(confirmed[(confirmed['falla_predicha'] == True) & (confirmed['timestamp_real_falla'].isna())])
        fn = len(confirmed[(confirmed['falla_predicha'] == False) & (confirmed['timestamp_real_falla'].notna())])
        tn = len(confirmed[(confirmed['falla_predicha'] == False) & (confirmed['timestamp_real_falla'].isna())])
        
        vcol1, vcol2, vcol3, vcol4 = st.columns(4)
        with vcol1:
            st.metric("Verdaderos Positivos", tp)
        with vcol2:
            st.metric("Falsos Positivos", fp)
        with vcol3:
            st.metric("Falsos Negativos", fn)
        with vcol4:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            st.metric("Precision / Recall", f"{precision:.1%} / {recall:.1%}")
    
    # Detailed table
    st.markdown("---")
    st.markdown("### 📋 Detalle de Predicciones")
    
    # Format for display
    display_df = df.copy()
    display_df['falla_predicha'] = display_df['falla_predicha'].map({True: '🔴 Falla', False: '🟢 Normal'})
    display_df['confianza'] = display_df['confianza'].apply(lambda x: f"{x:.1%}")
    display_df['tiene_falla_real'] = display_df['timestamp_real_falla'].apply(lambda x: '✅ Sí' if pd.notna(x) else '❌ No')
    
    # Filter UI
    filtered_df = filter_dataframe_ui(display_df, "history")
    paginated_dataframe(filtered_df, key="history_table")

def load_predictions_history(days_back: int, equipo_filter: str, model_filter: str, status_filter: str):
    """Load predictions history from database"""
    try:
        where_conditions = ["p.timestamp_prediccion >= %s"]
        params = [datetime.now() - timedelta(days=days_back)]
        
        if equipo_filter != "Todos":
            equipo_id = int(equipo_filter.split("ID: ")[1].split(")")[0])
            where_conditions.append("p.equipo_id = %s")
            params.append(equipo_id)
        
        if model_filter != "Todos":
            where_conditions.append("m.nombre = %s")
            params.append(model_filter)
        
        if status_filter == "Falla Predicha":
            where_conditions.append("p.falla_predicha = true")
        elif status_filter == "Normal":
            where_conditions.append("p.falla_predicha = false")
        elif status_filter == "Confirmada":
            where_conditions.append("p.timestamp_real_falla IS NOT NULL")
        elif status_filter == "Falso Positivo":
            where_conditions.append("p.falla_predicha = true AND p.timestamp_real_falla IS NULL")
        
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                p.id,
                p.timestamp_prediccion,
                e.codigo as equipo_codigo,
                e.nombre as equipo_nombre,
                m.nombre as modelo_nombre,
                p.falla_predicha,
                p.confianza,
                p.timestamp_real_falla,
                u.nombre as usuario_ejecutor
            FROM predicciones p
            JOIN equipos e ON e.id = p.equipo_id
            JOIN modelos_ia m ON m.id = p.modelo_id
            LEFT JOIN usuarios u ON u.id = p.usuario_ejecutor
            {where_clause}
            ORDER BY p.timestamp_prediccion DESC
            LIMIT 5000
        """
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        st.error(f"Error cargando historial: {e}")
        return pd.DataFrame()

def get_equipos_list():
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT id, codigo FROM equipos WHERE estado = 'activo' ORDER BY codigo")
            return [f"{row['codigo']} (ID: {row['id']})" for row in cursor.fetchall()]
    except:
        return []

def get_models_list():
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT nombre FROM modelos_ia WHERE activo = true ORDER BY fecha_entrenamiento DESC")
            return [row['nombre'] for row in cursor.fetchall()]
    except:
        return []

if __name__ == "__main__":
    render_history()