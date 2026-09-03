import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.db.connection import db_pool
from ui.components import (create_kpi_card, plot_time_series, paginated_dataframe, 
                          filter_dataframe_ui, render_business_objectives, 
                          render_crisp_dm_phase_indicator, show_loading)

def render_dashboard():
    render_crisp_dm_phase_indicator(1)
    render_business_objectives()
    
    st.markdown("---")
    st.markdown("## 📊 Dashboard Principal")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        days_back = st.selectbox("Período", [7, 30, 90, 365], index=1, format_func=lambda x: f"Últimos {x} días")
    with col2:
        equipo_filter = st.selectbox("Equipo", ["Todos"] + get_equipos_list())
    with col3:
        auto_refresh = st.checkbox("Auto-actualizar (30s)", value=False)
    
    if auto_refresh:
        st.experimental_rerun()
    
    # Load data
    with show_loading("Cargando métricas..."):
        kpis = load_kpis(days_back, equipo_filter)
        alerts = load_recent_alerts(days_back, equipo_filter)
        sensor_data = load_sensor_evolution(days_back, equipo_filter)
    
    # KPIs Row
    st.markdown("### 📈 Indicadores Clave (KPIs)")
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        create_kpi_card("Equipos Activos", str(kpis.get('active_equipos', 0)))
    with kpi_cols[1]:
        create_kpi_card("Disponibilidad Promedio", f"{kpis.get('availability', 0):.1f}%", 
                       delta=f"{kpis.get('availability_change', 0):+.1f}%")
    with kpi_cols[2]:
        create_kpi_card("Fallas Detectadas", str(kpis.get('failures_detected', 0)),
                       delta=f"{kpis.get('failures_change', 0):+d}")
    with kpi_cols[3]:
        create_kpi_card("MTTR (horas)", f"{kpis.get('mttr', 0):.1f}",
                       delta=f"{kpis.get('mttr_change', 0):+.1f}", delta_color="inverse")
    
    st.markdown("---")
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### 📈 Evolución de Sensores")
        if not sensor_data.empty:
            sensor_type = st.selectbox("Tipo de sensor", sensor_data['tipo_sensor'].unique())
            sensor_df = sensor_data[sensor_data['tipo_sensor'] == sensor_type]
            fig = px.line(sensor_df, x='timestamp', y='valor', color='equipo_codigo',
                         title=f"{sensor_type.capitalize()} por Equipo")
            fig.update_layout(height=400, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            show_info("No hay datos de sensores para el período seleccionado")
    
    with chart_col2:
        st.markdown("### 🚨 Alertas Recientes")
        if not alerts.empty:
            # Alert summary by type
            alert_summary = alerts.groupby('tipo_sensor').size().reset_index(name='count')
            fig = px.bar(alert_summary, x='tipo_sensor', y='count', 
                        title="Alertas por Tipo de Sensor", color='tipo_sensor')
            fig.update_layout(height=400, template='plotly_white', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts table
            st.markdown("#### Últimas Alertas")
            display_alerts = alerts[['timestamp', 'equipo_codigo', 'tipo_sensor', 'valor', 'calidad_dato']].head(10)
            display_alerts['calidad_dato'] = display_alerts['calidad_dato'].map({0: '✅ OK', 1: '⚠️ Alerta', 2: '🔴 Falla'})
            st.dataframe(display_alerts, use_container_width=True, hide_index=True)
        else:
            show_info("No hay alertas recientes")
    
    # Equipment Health Table
    st.markdown("### 🏥 Estado de Salud de Equipos")
    health_data = load_equipment_health()
    if not health_data.empty:
        filtered_health = filter_dataframe_ui(health_data, "health")
        paginated_dataframe(filtered_health, key="health_table")
    else:
        show_info("No hay datos de salud de equipos")

def get_equipos_list():
    """Get list of equipment codes"""
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT codigo FROM equipos WHERE estado = 'activo' ORDER BY codigo")
            return [row['codigo'] for row in cursor.fetchall()]
    except:
        return []

def load_kpis(days_back: int, equipo_filter: str):
    """Load KPI metrics"""
    try:
        where_clause = "WHERE l.timestamp >= %s"
        params = [datetime.now() - timedelta(days=days_back)]
        
        if equipo_filter != "Todos":
            where_clause += " AND e.codigo = %s"
            params.append(equipo_filter)
        
        query = f"""
            SELECT 
                COUNT(DISTINCT e.id) as active_equipos,
                AVG(CASE WHEN l.calidad_dato = 0 THEN 1 ELSE 0 END) * 100 as availability,
                COUNT(CASE WHEN l.calidad_dato = 2 THEN 1 END) as failures_detected
            FROM equipos e
            JOIN sensores s ON s.equipo_id = e.id AND s.activo = true
            JOIN lecturas l ON l.sensor_id = s.id
            {where_clause}
        """
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            
        return {
            'active_equipos': result['active_equipos'] or 0,
            'availability': float(result['availability'] or 0),
            'failures_detected': result['failures_detected'] or 0,
            'availability_change': 2.5,  # Mock
            'failures_change': -3,  # Mock
            'mttr': 4.2,  # Mock
            'mttr_change': -0.5  # Mock
        }
    except Exception as e:
        st.error(f"Error cargando KPIs: {e}")
        return {'active_equipos': 0, 'availability': 0, 'failures_detected': 0,
                'availability_change': 0, 'failures_change': 0, 'mttr': 0, 'mttr_change': 0}

def load_recent_alerts(days_back: int, equipo_filter: str):
    """Load recent alerts"""
    try:
        where_clause = "WHERE l.timestamp >= %s AND l.calidad_dato > 0"
        params = [datetime.now() - timedelta(days=days_back)]
        
        if equipo_filter != "Todos":
            where_clause += " AND e.codigo = %s"
            params.append(equipo_filter)
        
        query = f"""
            SELECT l.timestamp, e.codigo as equipo_codigo, s.tipo_sensor, 
                   l.valor, l.calidad_dato
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            JOIN equipos e ON e.id = s.equipo_id
            {where_clause}
            ORDER BY l.timestamp DESC
            LIMIT 100
        """
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        st.error(f"Error cargando alertas: {e}")
        return pd.DataFrame()

def load_sensor_evolution(days_back: int, equipo_filter: str):
    """Load sensor evolution data"""
    try:
        where_clause = "WHERE l.timestamp >= %s"
        params = [datetime.now() - timedelta(days=days_back)]
        
        if equipo_filter != "Todos":
            where_clause += " AND e.codigo = %s"
            params.append(equipo_filter)
        
        query = f"""
            SELECT l.timestamp, e.codigo as equipo_codigo, s.tipo_sensor, l.valor
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            JOIN equipos e ON e.id = s.equipo_id
            {where_clause}
            ORDER BY l.timestamp
            LIMIT 5000
        """
        
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        st.error(f"Error cargando evolución: {e}")
        return pd.DataFrame()

def load_equipment_health():
    """Load equipment health summary"""
    try:
        query = "SELECT * FROM v_resumen_salud_equipos"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        st.error(f"Error cargando salud de equipos: {e}")
        return pd.DataFrame()