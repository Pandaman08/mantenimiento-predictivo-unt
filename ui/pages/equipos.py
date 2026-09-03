import streamlit as st
import pandas as pd
from src.db.connection import db_pool
from ui.components import show_loading, show_success, show_error, show_info, paginated_dataframe, filter_dataframe_ui

def render_equipos():
    st.markdown("## 🚜 Gestión de Equipos y Sensores")
    
    tabs = st.tabs(["📋 Equipos", "📡 Sensores", "➕ Agregar"])
    
    with tabs[0]:
        render_equipos_list()
    
    with tabs[1]:
        render_sensores_list()
    
    with tabs[2]:
        render_add_forms()

def render_equipos_list():
    """List and manage equipment"""
    st.markdown("### 📋 Lista de Equipos")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_filter = st.selectbox("Tipo", ["Todos", "pala", "camion", "perforadora"])
    with col2:
        estado_filter = st.selectbox("Estado", ["Todos", "activo", "inactivo", "mantenimiento"])
    with col3:
        search = st.text_input("Buscar por código/nombre")
    
    # Load data
    equipos = load_equipos(tipo_filter, estado_filter, search)
    
    if not equipos.empty:
        # Summary
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Total", len(equipos))
        with mcol2:
            st.metric("Activos", len(equipos[equipos['estado'] == 'activo']))
        with mcol3:
            st.metric("En Mantenimiento", len(equipos[equipos['estado'] == 'mantenimiento']))
        with mcol4:
            st.metric("Inactivos", len(equipos[equipos['estado'] == 'inactivo']))
        
        # Table with actions
        st.markdown("#### Detalle")
        for _, eq in equipos.iterrows():
            with st.expander(f"{eq['codigo']} - {eq['nombre']} ({eq['tipo'].capitalize()})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Estado:** {eq['estado']}")
                    st.write(f"**Ubicación:** {eq.get('ubicacion', 'N/A')}")
                    st.write(f"**Fabricante:** {eq.get('fabricante', 'N/A')}")
                    st.write(f"**Modelo:** {eq.get('modelo', 'N/A')}")
                    st.write(f"**N° Serie:** {eq.get('numero_serie', 'N/A')}")
                    st.write(f"**Instalación:** {eq['fecha_instalacion']}")
                with col2:
                    # Sensors for this equipment
                    sensors = load_sensores_by_equipo(eq['id'])
                    st.write(f"**Sensores ({len(sensors)}):**")
                    for _, sen in sensors.iterrows():
                        status = "🟢" if sen['activo'] else "🔴"
                        st.write(f"  {status} {sen['tipo_sensor'].capitalize()} ({sen['unidad_medida']})")
                    
                    # Actions
                    st.markdown("---")
                    a_col1, a_col2, a_col3 = st.columns(3)
                    with a_col1:
                        new_status = st.selectbox("Cambiar estado", ["activo", "inactivo", "mantenimiento"],
                                                index=["activo", "inactivo", "mantenimiento"].index(eq['estado']),
                                                key=f"status_{eq['id']}")
                        if new_status != eq['estado']:
                            if st.button("Actualizar", key(f"upd_status_{eq['id']}")):
                                update_equipo_status(eq['id'], new_status)
                    with a_col2:
                        if st.button("📊 Ver Salud", key=f"health_{eq['id']}"):
                            st.session_state.current_page = 'dashboard'
                            st.rerun()
                    with a_col3:
                        if st.button("🗑️", key=f"del_eq_{eq['id']}"):
                            delete_equipo(eq['id'])
    else:
        show_info("No hay equipos registrados")

def render_sensores_list():
    """List sensors"""
    st.markdown("### 📡 Sensores")
    
    sensores = load_all_sensores()
    
    if not sensores.empty:
        # Filter
        filtered = filter_dataframe_ui(sensores, "sensores")
        
        # Display
        for _, sen in filtered.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    st.write(f"**{sen['equipo_codigo']}** - {sen['tipo_sensor'].capitalize()}")
                with col2:
                    st.write(f"{sen['unidad_medida']}")
                with col3:
                    st.write(f"Rango: {sen['rango_min']} - {sen['rango_max']}")
                with col4:
                    st.write("🟢 Activo" if sen['activo'] else "🔴 Inactivo")
                with col5:
                    if st.button("🗑️", key=f"del_sen_{sen['id']}"):
                        delete_sensor(sen['id'])
                st.divider()
    else:
        show_info("No hay sensores registrados")

def render_add_forms():
    """Forms to add equipment and sensors"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ➕ Agregar Equipo")
        with st.form("add_equipo"):
            codigo = st.text_input("Código *", placeholder="PAL-001")
            nombre = st.text_input("Nombre *", placeholder="Pala Hidráulica PH-001")
            tipo = st.selectbox("Tipo *", ["pala", "camion", "perforadora"])
            fecha_inst = st.date_input("Fecha Instalación *")
            ubicacion = st.text_input("Ubicación")
            fabricante = st.text_input("Fabricante")
            modelo = st.text_input("Modelo")
            n_serie = st.text_input("Número de Serie")
            
            if st.form_submit_button("Crear Equipo", type="primary"):
                if codigo and nombre:
                    create_equipo(codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie)
                else:
                    show_error("Código y nombre son obligatorios")
    
    with col2:
        st.markdown("### ➕ Agregar Sensor")
        with st.form("add_sensor"):
            equipo_id = st.selectbox("Equipo *", get_equipos_for_select())
            tipo_sensor = st.selectbox("Tipo Sensor *", ["temperatura", "presion_aceite", "rpm", "vibracion", "horas_operacion"])
            unidad = st.text_input("Unidad *", placeholder="°C, PSI, RPM, mm/s, horas")
            rango_min = st.number_input("Rango Mín", value=0.0)
            rango_max = st.number_input("Rango Máx", value=100.0)
            ubicacion = st.text_input("Ubicación en equipo")
            
            if st.form_submit_button("Crear Sensor", type="primary"):
                if equipo_id and tipo_sensor and unidad:
                    create_sensor(equipo_id, tipo_sensor, unidad, rango_min, rango_max, ubicacion)
                else:
                    show_error("Complete campos obligatorios")

# Database operations
def load_equipos(tipo_filter, estado_filter, search):
    try:
        conditions = []
        params = []
        
        if tipo_filter != "Todos":
            conditions.append("tipo = %s")
            params.append(tipo_filter)
        if estado_filter != "Todos":
            conditions.append("estado = %s")
            params.append(estado_filter)
        if search:
            conditions.append("(codigo ILIKE %s OR nombre ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"SELECT * FROM equipos {where} ORDER BY fecha_creacion DESC"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        show_error(f"Error: {e}")
        return pd.DataFrame()

def load_sensores_by_equipo(equipo_id: int):
    try:
        query = "SELECT * FROM sensores WHERE equipo_id = %s ORDER BY tipo_sensor"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (equipo_id,))
            return pd.DataFrame(cursor.fetchall())
    except:
        return pd.DataFrame()

def load_all_sensores():
    try:
        query = """
            SELECT s.*, e.codigo as equipo_codigo
            FROM sensores s
            JOIN equipos e ON e.id = s.equipo_id
            ORDER BY e.codigo, s.tipo_sensor
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall())
    except:
        return pd.DataFrame()

def get_equipos_for_select():
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT id, codigo FROM equipos WHERE estado = 'activo' ORDER BY codigo")
            return {f"{row['codigo']} (ID: {row['id']})": row['id'] for row in cursor.fetchall()}
    except:
        return {}

def create_equipo(codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie):
    try:
        query = """
            INSERT INTO equipos (codigo, nombre, tipo, fecha_instalacion, ubicacion, fabricante, modelo, numero_serie)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie))
        show_success(f"Equipo {codigo} creado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

def create_sensor(equipo_id, tipo_sensor, unidad, rango_min, rango_max, ubicacion):
    try:
        # Parse equipo_id from selection string
        eq_id = int(equipo_id.split("ID: ")[1].split(")")[0])
        
        query = """
            INSERT INTO sensores (equipo_id, tipo_sensor, unidad_medida, rango_min, rango_max, ubicacion_sensor)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (eq_id, tipo_sensor, unidad, rango_min, rango_max, ubicacion))
        show_success("Sensor creado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

def update_equipo_status(equipo_id: int, new_status: str):
    try:
        query = "UPDATE equipos SET estado = %s WHERE id = %s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (new_status, equipo_id))
        show_success("Estado actualizado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

def delete_equipo(equipo_id: int):
    try:
        query = "DELETE FROM equipos WHERE id = %s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (equipo_id,))
        show_success("Equipo eliminado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

def delete_sensor(sensor_id: int):
    try:
        query = "DELETE FROM sensores WHERE id = %s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (sensor_id,))
        show_success("Sensor eliminado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

if __name__ == "__main__":
    render_equipos()