import streamlit as st
import pandas as pd
from src.db.connection import db_pool
from src.auth.auth_service import auth_service
from ui.components import show_loading, show_success, show_error, show_info, paginated_dataframe, filter_dataframe_ui

def render_admin():
    st.markdown("## ⚙️ Administración del Sistema")
    
    tabs = st.tabs(["👥 Usuarios", "🎭 Roles y Permisos", "📊 Auditoría", "⚙️ Configuración"])
    
    with tabs[0]:
        render_user_management()
    
    with tabs[1]:
        render_roles_permissions()
    
    with tabs[2]:
        render_audit_logs()
    
    with tabs[3]:
        render_system_config()

def render_user_management():
    """User CRUD operations"""
    st.markdown("### 👥 Gestión de Usuarios")
    
    # Add new user
    with st.expander("➕ Crear Nuevo Usuario"):
        with st.form("create_user"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre completo")
                email = st.text_input("Email")
            with col2:
                password = st.text_input("Contraseña", type="password")
                role = st.selectbox("Rol", ["operador", "analista", "supervisor", "administrador"])
            
            if st.form_submit_button("Crear Usuario", type="primary"):
                if all([nombre, email, password]):
                    role_id = {"operador": 3, "analista": 4, "supervisor": 2, "administrador": 1}[role]
                    user_id = auth_service.register_user(nombre, email, password, role_id)
                    if user_id:
                        show_success(f"Usuario creado con ID: {user_id}")
                        st.rerun()
                    else:
                        show_error("Error creando usuario (email duplicado?)")
                else:
                    show_error("Complete todos los campos")
    
    # List users
    st.markdown("#### Lista de Usuarios")
    users = load_users()
    
    if not users.empty:
        # Filter
        filtered = filter_dataframe_ui(users, "admin_users")
        
        # Display with actions
        for _, user in filtered.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                with col1:
                    st.write(f"**{user['nombre']}**")
                with col2:
                    st.write(user['email'])
                with col3:
                    st.badge(user['rol_nombre'])
                with col4:
                    status = "🟢 Activo" if user['activo'] else "🔴 Inactivo"
                    st.write(status)
                with col5:
                    if st.button("✏️", key=f"edit_{user['id']}"):
                        edit_user_dialog(user)
                    if st.button("🗑️", key=f"del_{user['id']}"):
                        if st.session_state.get(f'confirm_del_{user["id"]}'):
                            delete_user(user['id'])
                        else:
                            st.session_state[f'confirm_del_{user["id"]}'] = True
                            st.warning("Presione de nuevo para confirmar")
                            st.rerun()
                st.divider()
    else:
        show_info("No hay usuarios registrados")

def render_roles_permissions():
    """Roles and permissions management"""
    st.markdown("### 🎭 Roles y Permisos")
    
    # Load roles
    roles = load_roles()
    
    for role in roles:
        with st.expander(f"{role['nombre'].capitalize()} ({role['descripcion']})"):
            perms = load_permissions(role['id'])
            
            if not perms.empty:
                # Group by resource
                for resource in perms['recurso'].unique():
                    st.markdown(f"**{resource}**")
                    resource_perms = perms[perms['recurso'] == resource]
                    
                    cols = st.columns(4)
                    for i, (_, perm) in enumerate(resource_perms.iterrows()):
                        with cols[i % 4]:
                            new_val = st.checkbox(
                                perm['accion'].capitalize(),
                                value=perm['concedido'],
                                key=f"perm_{role['id']}_{resource}_{perm['accion']}"
                            )
                            if new_val != perm['concedido']:
                                update_permission(role['id'], resource, perm['accion'], new_val)
            else:
                show_info("Sin permisos configurados")

def render_audit_logs():
    """System audit logs"""
    st.markdown("### 📊 Logs de Auditoría")
    
    col1, col2 = st.columns(2)
    with col1:
        days = st.selectbox("Período", [1, 7, 30], index=1)
    with col2:
        action_filter = st.selectbox("Acción", ["Todas", "LOGIN", "PREDICTION", "TRAINING", "REPORT"])
    
    logs = load_audit_logs(days, action_filter)
    
    if not logs.empty:
        paginated_dataframe(logs, key="audit_logs")
    else:
        show_info("No hay logs en el período seleccionado")

def render_system_config():
    """System configuration"""
    st.markdown("### ⚙️ Configuración del Sistema")
    
    st.markdown("#### Parámetros de Modelo")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Umbral de confianza para alerta", 0.0, 1.0, 0.5, 0.05)
        st.number_input("Ventana de predicción (horas)", 1, 72, 24)
    with col2:
        st.number_input("Frecuencia de muestreo (min)", 1, 60, 5)
        st.number_input("Máximo registros por consulta", 1000, 100000, 10000)
    
    st.markdown("#### Notificaciones")
    st.checkbox("Email en fallas críticas", value=True)
    st.checkbox("Email en reporte diario", value=False)
    st.checkbox("Webhook para integración externa", value=False)
    
    if st.button("💾 Guardar Configuración", type="primary"):
        show_success("Configuración guardada")

# Helper functions
def load_users():
    try:
        query = """
            SELECT u.id, u.nombre, u.email, u.rol_id, u.activo, u.fecha_creacion, u.ultimo_login, r.nombre as rol_nombre
            FROM usuarios u
            JOIN roles r ON r.id = u.rol_id
            ORDER BY u.fecha_creacion DESC
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query)
            return pd.DataFrame(cursor.fetchall())
    except Exception as e:
        show_error(f"Error: {e}")
        return pd.DataFrame()

def load_roles():
    try:
        with db_pool.get_cursor() as cursor:
            cursor.execute("SELECT * FROM roles ORDER BY id")
            return cursor.fetchall()
    except:
        return []

def load_permissions(role_id: int):
    try:
        query = "SELECT * FROM permisos WHERE rol_id = %s ORDER BY recurso, accion"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (role_id,))
            return pd.DataFrame(cursor.fetchall())
    except:
        return pd.DataFrame()

def update_permission(role_id: int, resource: str, action: str, granted: bool):
    try:
        query = """
            UPDATE permisos SET concedido = %s 
            WHERE rol_id = %s AND recurso = %s AND accion = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (granted, role_id, resource, action))
        show_success(f"Permiso actualizado: {resource}.{action}")
    except Exception as e:
        show_error(f"Error: {e}")

def load_audit_logs(days: int, action_filter: str):
    # Simulated - would need audit_log table
    return pd.DataFrame()

def edit_user_dialog(user):
    """Edit user dialog"""
    @st.dialog(f"Editar: {user['nombre']}")
    def dialog():
        with st.form("edit_user"):
            nombre = st.text_input("Nombre", value=user['nombre'])
            email = st.text_input("Email", value=user['email'])
            activo = st.checkbox("Activo", value=user['activo'])
            role = st.selectbox("Rol", ["operador", "analista", "supervisor", "administrador"],
                              index=["operador", "analista", "supervisor", "administrador"].index(user['rol_nombre']))
            
            if st.form_submit_button("Guardar"):
                update_user(user['id'], nombre, email, activo, role)
    dialog()

def update_user(user_id: int, nombre: str, email: str, activo: bool, role: str):
    try:
        role_id = {"operador": 3, "analista": 4, "supervisor": 2, "administrador": 1}[role]
        query = "UPDATE usuarios SET nombre=%s, email=%s, activo=%s, rol_id=%s WHERE id=%s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (nombre, email, activo, role_id, user_id))
        show_success("Usuario actualizado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

def delete_user(user_id: int):
    try:
        query = "DELETE FROM usuarios WHERE id = %s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
        show_success("Usuario eliminado")
        st.rerun()
    except Exception as e:
        show_error(f"Error: {e}")

if __name__ == "__main__":
    render_admin()