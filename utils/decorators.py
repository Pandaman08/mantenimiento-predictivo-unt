import streamlit as st


def requires_permission(resource: str, action: str = 'leer'):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get('authenticated', False):
                st.warning('Debe iniciar sesión para acceder a esta funcionalidad.')
                st.stop()

            user = st.session_state.get('user') or {}
            role = user.get('role') or 'operador'
            permissions = st.session_state.get('permissions', [])
            if not permissions:
                permissions = [
                    {'resource': 'dashboard', 'action': 'leer'},
                    {'resource': 'prediccion', 'action': 'leer'},
                    {'resource': 'prediccion', 'action': 'ejecutar'},
                    {'resource': 'reportes', 'action': 'ejecutar'},
                    {'resource': 'entrenamiento', 'action': 'ejecutar'},
                ]
                if role in ('administrador', 'analista', 'supervisor'):
                    permissions.extend([
                        {'resource': 'dashboard', 'action': 'leer'},
                        {'resource': 'reportes', 'action': 'leer'},
                        {'resource': 'entrenamiento', 'action': 'leer'},
                        {'resource': 'evaluacion', 'action': 'ejecutar'},
                    ])
            allowed = any(
                p.get('resource') == resource and p.get('action') == action for p in permissions
            )
            if not allowed:
                st.error(f'No cuenta con permisos para {resource} ({action}).')
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator
