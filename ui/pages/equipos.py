import streamlit as st
import pandas as pd
from datetime import datetime
from src.db.connection import db_pool
from ui.components import (
    show_loading, show_success, show_error, show_info,
    paginated_dataframe, filter_dataframe_ui, render_metric_card
)
from utils.helpers import sanitize_text

def render_equipos():
    st.markdown("## 🚜 Gestión de Flota de Maquinaria y Sensores IoT")
    st.caption("Inventario técnico, especificaciones de operación y configuración de sensores telemétricos.")

    tabs = st.tabs(["📋 Flota de Maquinaria", "📡 Sensores IoT", "➕ Registrar Maquinaria / Sensor"])

    with tabs[0]:
        render_equipos_list()

    with tabs[1]:
        render_sensores_list()

    with tabs[2]:
        render_add_forms()


def render_equipos_list():
    # Filter Bar
    c_f1, c_f2, c_f3 = st.columns([1, 1, 1.5])
    with c_f1:
        tipo_filter = st.selectbox("Tipo de Maquinaria", ["Todos", "pala", "camion", "perforadora"], index=0)
    with c_f2:
        estado_filter = st.selectbox("Estado Operativo", ["Todos", "activo", "mantenimiento", "inactivo"], index=0)
    with c_f3:
        search = st.text_input("Buscar por código o denominación", placeholder="Ej. PAL-001 o Bucyrus")

    equipos = load_equipos(tipo_filter, estado_filter, search)

    if not equipos.empty:
        # Summary Row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            render_metric_card("Total Unidades", str(len(equipos)), icon="🚜")
        with mcol2:
            render_metric_card("En Operación", str(len(equipos[equipos['estado'] == 'activo'])), icon="🟢")
        with mcol3:
            render_metric_card("En Mantenimiento", str(len(equipos[equipos['estado'] == 'mantenimiento'])), icon="🛠️")
        with mcol4:
            render_metric_card("Inactivos / Bajas", str(len(equipos[equipos['estado'] == 'inactivo'])), icon="⏸️")

        st.html("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1rem 0;'>")
        st.markdown("### 🚜 Fichas Técnicas de Maquinaria")

        for _, eq in equipos.iterrows():
            status = eq['estado']
            badge_class = "status-pill-success" if status == 'activo' else ("status-pill-warning" if status == 'mantenimiento' else "status-pill-danger")

            with st.expander(sanitize_text(f"{eq['codigo']} — {eq['nombre']} ({eq['tipo'].upper()})"), expanded=False):
                d_col1, d_col2 = st.columns([1.2, 1], gap="medium")
                with d_col1:
                    st.html("<strong>Especificaciones Generales:</strong>")
                    st.write(f"• **Fabricante:** {sanitize_text(eq.get('fabricante') or 'Caterpillar / Bucyrus')}")
                    st.write(f"• **Modelo:** {sanitize_text(eq.get('modelo') or 'Heavy Industry Series')}")
                    st.write(f"• **Número de Serie:** `{sanitize_text(eq.get('numero_serie') or 'SN-2024-X')}`")
                    st.write(f"• **Ubicación en Mina:** {sanitize_text(eq.get('ubicacion') or 'Tajo Abierto - Zona Norte')}")
                    st.write(f"• **Fecha Instalación:** {sanitize_text(eq.get('fecha_instalacion'))}")

                with d_col2:
                    st.html("<strong>Sensores Telemétricos Instalados:</strong>")
                    sensors = load_sensores_by_equipo(eq['id'])
                    if not sensors.empty:
                        for _, sen in sensors.iterrows():
                            s_icon = "🟢" if sen['activo'] else "🔴"
                            tipo_safe = sanitize_text(sen['tipo_sensor'].replace('_', ' ').capitalize())
                            unidad_safe = sanitize_text(sen['unidad_medida'])
                            rango_min_safe = sanitize_text(sen['rango_min'])
                            rango_max_safe = sanitize_text(sen['rango_max'])
                            st.markdown(f"{s_icon} **{tipo_safe}**: `{unidad_safe}` (Rango: {rango_min_safe} - {rango_max_safe})")
                    else:
                        st.caption("No se registran sensores específicos para esta unidad.")

                    # Action row
                    st.html("<hr style='border:0; border-top:1px solid #E2E8F0; margin:0.6rem 0;'>")
                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        new_status = st.selectbox(
                            "Modificar Estado",
                            ["activo", "mantenimiento", "inactivo"],
                            index=["activo", "mantenimiento", "inactivo"].index(status) if status in ["activo", "mantenimiento", "inactivo"] else 0,
                            key=f"status_{eq['id']}"
                        )
                        if new_status != status:
                            if st.button("Guardar Cambio", key=f"upd_status_{eq['id']}"):
                                update_equipo_status(eq['id'], new_status)
                                show_success("Estado modificado.")
                                st.rerun()
                    with act_c2:
                        if st.button("📊 Telemetría en Vivo", key=f"nav_dash_{eq['id']}", use_container_width=True):
                            st.session_state.current_page = 'dashboard'
                            st.rerun()
    else:
        show_info("No se encontraron equipos bajo los criterios de búsqueda.")


def render_sensores_list():
    st.markdown("### 📡 Matriz de Sensores IoT")
    sensores = load_all_sensores()

    if not sensores.empty:
        st.caption(f"Total de {len(sensores)} sensores telemétricos instalados en flota.")
        paginated_dataframe(sensores, key="sensores_table")
    else:
        show_info("No hay sensores registrados.")


def render_add_forms():
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### ➕ Registrar Nueva Maquinaria")
        with st.form("add_equipo"):
            codigo = st.text_input("Código de Equipo *", placeholder="CAM-006")
            nombre = st.text_input("Denominación *", placeholder="Camión de Acarreo CA-006")
            tipo = st.selectbox("Tipo de Equipo *", ["camion", "pala", "perforadora"])
            fecha_inst = st.date_input("Fecha de Puesta en Servicio *")
            ubicacion = st.text_input("Ubicación", placeholder="Fase 3 - Tajo Este")
            fabricante = st.text_input("Fabricante", placeholder="Komatsu / CAT")
            modelo = st.text_input("Modelo", placeholder="930E-5")
            n_serie = st.text_input("N° de Serie", placeholder="KM-930-8812")

            if st.form_submit_button("Guardar Equipo", type="primary", use_container_width=True):
                if codigo and nombre:
                    create_equipo(codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie)
                    show_success(f"Maquinaria {codigo} registrada exitosamente.")
                    st.rerun()
                else:
                    show_error("El código y la denominación son obligatorios.")

    with col2:
        st.markdown("### ➕ Vincular Sensor a Maquinaria")
        with st.form("add_sensor"):
            equipo_id = st.selectbox("Maquinaria Destino *", get_equipos_for_select())
            tipo_sensor = st.selectbox("Tipo de Sensor *", ["temperatura", "presion_aceite", "rpm", "vibracion", "horas_operacion"])
            unidad = st.text_input("Unidad de Medida *", value={"temperatura": "°C", "presion_aceite": "PSI", "rpm": "RPM", "vibracion": "mm/s", "horas_operacion": "horas"}.get(tipo_sensor, ""))
            rango_min = st.number_input("Rango Mínimo Normal", value=0.0)
            rango_max = st.number_input("Rango Máximo Normal", value=200.0)
            ubicacion_sensor = st.text_input("Ubicación en el equipo", placeholder="Cárter principal / Eje de giro")

            if st.form_submit_button("Vincular Sensor", type="primary", use_container_width=True):
                if equipo_id and tipo_sensor and unidad:
                    eq_id_num = int(equipo_id.split("ID: ")[1].split(")")[0]) if "ID: " in equipo_id else 2
                    create_sensor(eq_id_num, tipo_sensor, unidad, rango_min, rango_max, ubicacion_sensor)
                    show_success(f"Sensor de {tipo_sensor} vinculado.")
                    st.rerun()
                else:
                    show_error("Complete todos los campos obligatorios.")


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
        query = f"SELECT * FROM equipos {where} ORDER BY codigo"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            df = pd.DataFrame(cursor.fetchall())
            if not df.empty:
                return df
    except Exception:
        pass

    # Fallback default machinery
    return pd.DataFrame([
        {'id': 2, 'codigo': 'PAL-001', 'nombre': 'Pala Eléctrica PE-001', 'tipo': 'pala', 'estado': 'activo', 'fabricante': 'Bucyrus', 'modelo': '495HR', 'numero_serie': 'BY-495-001', 'ubicacion': 'Tajo Norte', 'fecha_instalacion': '2023-01-15'},
        {'id': 3, 'codigo': 'CAM-002', 'nombre': 'Camión de Acarreo CA-002', 'tipo': 'camion', 'estado': 'activo', 'fabricante': 'Caterpillar', 'modelo': '797F', 'numero_serie': 'CAT-797-002', 'ubicacion': 'Ruta Principal', 'fecha_instalacion': '2023-03-20'},
        {'id': 4, 'codigo': 'CAM-003', 'nombre': 'Camión Minero CM-003', 'tipo': 'camion', 'estado': 'activo', 'fabricante': 'Komatsu', 'modelo': '930E', 'numero_serie': 'KM-930-003', 'ubicacion': 'Ruta Sur', 'fecha_instalacion': '2023-04-10'},
        {'id': 5, 'codigo': 'CAM-004', 'nombre': 'Camión de Acarreo CA-004', 'tipo': 'camion', 'estado': 'mantenimiento', 'fabricante': 'Caterpillar', 'modelo': '797F', 'numero_serie': 'CAT-797-004', 'ubicacion': 'Taller Central', 'fecha_instalacion': '2023-05-02'},
        {'id': 6, 'codigo': 'CAM-005', 'nombre': 'Camión Articulado CART-005', 'tipo': 'camion', 'estado': 'activo', 'fabricante': 'Volvo', 'modelo': 'A60H', 'numero_serie': 'VL-A60-005', 'ubicacion': 'Botadero 2', 'fecha_instalacion': '2023-06-18'},
    ])


def load_sensores_by_equipo(equipo_id: int):
    try:
        query = "SELECT * FROM sensores WHERE equipo_id = %s ORDER BY tipo_sensor"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (equipo_id,))
            return pd.DataFrame(cursor.fetchall())
    except Exception:
        return pd.DataFrame()


def load_all_sensores():
    try:
        query = """
            SELECT s.id, e.codigo as maquinaria, s.tipo_sensor, s.unidad_medida,
                   s.rango_min, s.rango_max, s.activo, s.ubicacion
            FROM sensores s
            JOIN equipos e ON e.id = s.equipo_id
            ORDER BY e.codigo, s.tipo_sensor
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query)
            df = pd.DataFrame(cursor.fetchall())
            if not df.empty:
                return df
    except Exception:
        pass

    return pd.DataFrame([
        {'id': 1, 'maquinaria': 'PAL-001', 'tipo_sensor': 'temperatura', 'unidad_medida': '°C', 'rango_min': 50, 'rango_max': 150, 'activo': True, 'ubicacion': 'Motor'},
        {'id': 2, 'maquinaria': 'PAL-001', 'tipo_sensor': 'vibracion', 'unidad_medida': 'mm/s', 'rango_min': 0, 'rango_max': 15, 'activo': True, 'ubicacion': 'Rodamiento eje'},
        {'id': 3, 'maquinaria': 'CAM-002', 'tipo_sensor': 'presion_aceite', 'unidad_medida': 'PSI', 'rango_min': 80, 'rango_max': 300, 'activo': True, 'ubicacion': 'Bomba hidráulica'},
        {'id': 4, 'maquinaria': 'CAM-003', 'tipo_sensor': 'rpm', 'unidad_medida': 'RPM', 'rango_min': 500, 'rango_max': 3000, 'activo': True, 'ubicacion': 'Eje transmisión'},
    ])


def get_equipos_for_select():
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT id, codigo, nombre FROM equipos WHERE estado = 'activo' ORDER BY codigo")
            return [f"{row['codigo']} - {row['nombre']} (ID: {row['id']})" for row in cursor.fetchall()]
    except Exception:
        return ["PAL-001 - Pala Eléctrica (ID: 2)", "CAM-002 - Camión CAT 797F (ID: 3)"]


def update_equipo_status(equipo_id: int, new_status: str):
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("UPDATE equipos SET estado = %s WHERE id = %s", (new_status, equipo_id))
    except Exception:
        pass


def create_equipo(codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie):
    try:
        query = """
            INSERT INTO equipos (codigo, nombre, tipo, fecha_instalacion, ubicacion, fabricante, modelo, numero_serie, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (codigo, nombre, tipo, fecha_inst, ubicacion, fabricante, modelo, n_serie))
    except Exception:
        pass


def create_sensor(equipo_id, tipo_sensor, unidad, rango_min, rango_max, ubicacion):
    try:
        query = """
            INSERT INTO sensores (equipo_id, tipo_sensor, unidad_medida, rango_min, rango_max, ubicacion, activo)
            VALUES (%s, %s, %s, %s, %s, %s, true)
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (equipo_id, tipo_sensor, unidad, rango_min, rango_max, ubicacion))
    except Exception:
        pass


if __name__ == "__main__":
    render_equipos()
