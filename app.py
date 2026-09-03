import importlib
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.auth_service import auth_service
from src.db.connection import db_pool

DEFAULT_SESSION = {
    'authenticated': False,
    'user': None,
    'token': None,
    'current_page': 'login',
    'permissions': [],
    'sidebar_collapsed': False,
}

st.set_page_config(
    page_title='Sistema de Mantenimiento Predictivo - UNT',
    page_icon='🛠️',
    layout='wide',
    initial_sidebar_state='expanded',
)


def inject_custom_css():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            html, body, [class*='st'] { font-family: 'Inter', sans-serif; }
            .block-container { padding-top: 1.2rem; }
            :root {
                --unt-primary: #0A2B5E;
                --unt-primary-2: #123f80;
                --unt-gold: #C5A55A;
                --unt-surface: rgba(255,255,255,0.92);
                --unt-bg: #f3f7fb;
                --unt-text: #12263f;
                --unt-muted: #5f7189;
                --unt-border: rgba(10, 43, 94, 0.1);
                --unt-success: #1d8b5a;
                --unt-danger: #d94a4a;
            }
            html, body, [class*='stApp'] {
                background: linear-gradient(180deg, #edf3fb 0%, #f7f9fc 100%);
                color: var(--unt-text);
            }
            .block-container {
                padding-top: 1.4rem;
                padding-bottom: 3rem;
            }
            .unt-header {
                background: linear-gradient(135deg, var(--unt-primary) 0%, var(--unt-primary-2) 100%);
                border-radius: 18px;
                padding: 1.2rem 1.4rem;
                color: white;
                box-shadow: 0 14px 40px rgba(10, 43, 94, 0.18);
                margin-bottom: 1rem;
            }
            .unt-card {
                background: rgba(255,255,255,0.9);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 10px 26px rgba(15, 38, 65, 0.08);
                border: 1px solid var(--unt-border);
                backdrop-filter: blur(8px);
            }
            .role-badge {
                display: inline-block;
                padding: 0.35rem 0.8rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .role-administrador { background: var(--unt-primary); color: white; }
            .role-supervisor { background: #f7ebc3; color: var(--unt-primary); }
            .role-analista { background: #dfe8ff; color: var(--unt-primary); }
            .role-operador { background: #dff7ec; color: #1a6337; }
            .stSuccess > div { background: linear-gradient(90deg, #ecf9f2 0%, #f5fff9 100%); color: #0e6d42; border-left: 4px solid var(--unt-success); }
            .stError > div { background: linear-gradient(90deg, #fff1f1 0%, #fff8f8 100%); color: #9b2f2f; border-left: 4px solid var(--unt-danger); }
            .stInfo > div { background: linear-gradient(90deg, #edf5ff 0%, #f5f9ff 100%); color: #214a7d; border-left: 4px solid var(--unt-primary); }
            .stWarning > div { background: linear-gradient(90deg, #fff8e8 0%, #fffdf4 100%); color: #7a5400; border-left: 4px solid var(--unt-gold); }
            .stMetric > div {
                background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(244,248,253,0.96));
                border: 1px solid var(--unt-border);
                border-radius: 16px;
                padding: 0.8rem 0.9rem;
                box-shadow: 0 8px 18px rgba(17, 39, 69, 0.06);
            }
            .stButton > button {
                border-radius: 12px;
                border: 0;
                font-weight: 700;
                transition: all 0.2s ease;
                box-shadow: 0 8px 20px rgba(10,43,94,0.10);
            }
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 10px 24px rgba(10,43,94,0.16);
            }
            .stButton > button[kind='primary'] {
                background: linear-gradient(135deg, var(--unt-primary) 0%, var(--unt-primary-2) 100%);
                color: white;
            }
            .stButton > button[kind='secondary'] {
                background: white;
                color: var(--unt-primary);
                border: 1px solid var(--unt-border);
            }
            .sidebar .block-container { padding-top: 0.75rem; }
            [data-testid='stSidebar'] {
                background: linear-gradient(180deg, #0A2B5E 0%, #0f3a7b 100%);
                border-right: 1px solid rgba(255,255,255,0.12);
            }
            [data-testid='stSidebar'] * { color: white; }
            [data-testid='stSidebar'] .stButton > button {
                background: var(--unt-gold);
                color: var(--unt-primary);
                border: 0;
                border-radius: 12px;
                font-weight: 700;
            }
            [data-testid='stSidebar'] .stButton > button:hover { filter: brightness(1.05); }
            .login-shell {
                background: linear-gradient(135deg, rgba(10,43,94,0.96) 0%, rgba(26,75,144,0.96) 100%);
                border-radius: 26px;
                padding: 1.5rem;
                box-shadow: 0 20px 50px rgba(10, 43, 94, 0.18);
                margin: 0 auto 1.25rem auto;
            }
            .login-hero {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 22px;
                padding: 1.5rem;
                color: white;
            }
            .login-hero h1 {
                font-size: clamp(2rem, 3vw, 3rem);
                line-height: 1.1;
                margin-bottom: 0.5rem;
            }
            .login-panel {
                background: rgba(255,255,255,0.92);
                border-radius: 22px;
                padding: 1.1rem;
                border: 1px solid rgba(255,255,255,0.18);
            }
            @media (max-width: 768px) {
                .block-container { padding-left: 0.65rem; padding-right: 0.65rem; }
                .unt-header { padding: 1rem; }
                .login-shell { padding: 1rem; }
                .login-hero { margin-bottom: 1rem; }
                [data-testid='stSidebar'] { background: var(--unt-primary); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_custom_css()


def init_session_state():
    for key, value in DEFAULT_SESSION.items():
        st.session_state.setdefault(key, value)


def auth_required_page(page_name: str):
    if not st.session_state.get('authenticated'):
        st.session_state.current_page = 'login'
        st.rerun()


def has_permission(resource: str, action: str = 'leer') -> bool:
    if not st.session_state.get('authenticated'):
        return False
    role = (st.session_state.get('user') or {}).get('role') or 'operador'
    permissions = st.session_state.get('permissions') or []
    if not permissions:
        role_permissions = {
            'administrador': ['dashboard', 'modelos', 'reportes', 'usuarios', 'equipos', 'entrenamiento', 'prediccion', 'admin', 'evaluacion'],
            'supervisor': ['dashboard', 'reportes', 'equipos', 'prediccion'],
            'analista': ['dashboard', 'modelos', 'reportes', 'entrenamiento', 'evaluacion', 'prediccion'],
            'operador': ['dashboard', 'prediccion'],
        }
        permissions = [{'resource': item, 'action': 'leer'} for item in role_permissions.get(role, [])]
        if role in ['administrador', 'analista', 'supervisor']:
            permissions.append({'resource': 'prediccion', 'action': 'ejecutar'})
        st.session_state.permissions = permissions
    return any(p.get('resource') == resource and p.get('action') == action for p in permissions)


NAV_PAGES = {
    'administrador': [
        ('login', '🔐 Login', 'dashboard'),
        ('dashboard', '📊 Dashboard', 'dashboard'),
        ('01_Business_Understanding', '🏢 Negocio', 'dashboard'),
        ('02_Data_Understanding', '📈 EDA', 'dashboard'),
        ('03_Data_Preparation', '🧹 Preparación', 'entrenamiento'),
        ('04_Modeling', '🤖 Modelado', 'entrenamiento'),
        ('05_Evaluation', '📊 Evaluación', 'evaluacion'),
        ('06_Deployment', '🚀 Despliegue', 'prediccion'),
        ('reports', '📄 Reportes', 'reportes'),
    ],
    'supervisor': [
        ('dashboard', '📊 Dashboard', 'dashboard'),
        ('01_Business_Understanding', '🏢 Negocio', 'dashboard'),
        ('02_Data_Understanding', '📈 EDA', 'dashboard'),
        ('06_Deployment', '🚀 Despliegue', 'prediccion'),
        ('reports', '📄 Reportes', 'reportes'),
    ],
    'analista': [
        ('dashboard', '📊 Dashboard', 'dashboard'),
        ('01_Business_Understanding', '🏢 Negocio', 'dashboard'),
        ('02_Data_Understanding', '📈 EDA', 'dashboard'),
        ('03_Data_Preparation', '🧹 Preparación', 'entrenamiento'),
        ('04_Modeling', '🤖 Modelado', 'entrenamiento'),
        ('05_Evaluation', '📊 Evaluación', 'evaluacion'),
        ('06_Deployment', '🚀 Despliegue', 'prediccion'),
        ('reports', '📄 Reportes', 'reportes'),
    ],
    'operador': [
        ('dashboard', '📊 Dashboard', 'dashboard'),
        ('06_Deployment', '🚀 Despliegue', 'prediccion'),
    ],
}


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class='unt-header' style='text-align:center;'>
                <h3 style='margin:0; color:white;'>UNT</h3>
                <div style='font-size:0.83rem; opacity:0.9; margin-top:8px;'>Mantenimiento Predictivo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get('authenticated'):
            user = st.session_state.get('user') or {}
            role = user.get('role', 'operador')
            st.markdown(
                f"""
                <div class='unt-card' style='margin-bottom:1rem; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18);'>
                    <div><strong>{user.get('nombre', 'Usuario')}</strong></div>
                    <div style='font-size:0.8rem; opacity:0.9;'>{user.get('email', '')}</div>
                    <span class='role-badge role-{role}'>{role}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            pages = NAV_PAGES.get(role, NAV_PAGES['operador'])
            for page_key, page_label, perm_resource in pages:
                if has_permission(perm_resource, 'leer'):
                    button_type = 'primary' if st.session_state.get('current_page') == page_key else 'secondary'
                    if st.button(page_label, key=f'nav_{page_key}', use_container_width=True, type=button_type):
                        st.session_state.current_page = page_key
                        st.rerun()
            if st.button('🚪 Cerrar Sesión', use_container_width=True):
                for key in DEFAULT_SESSION:
                    st.session_state[key] = DEFAULT_SESSION[key]
                st.session_state.current_page = 'login'
                st.rerun()
        else:
            st.caption('Inicie sesión para continuar')


def require_permission(resource: str, action: str = 'leer'):
    if not has_permission(resource, action):
        st.error(f'No cuenta con permisos para {resource} ({action}).')
        st.stop()


def route_guard(page: str):
    if page == 'login':
        if st.session_state.get('authenticated'):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        return

    if not st.session_state.get('authenticated'):
        st.session_state.current_page = 'login'
        st.rerun()

    page_permissions = {
        'dashboard': ('dashboard', 'leer'),
        '01_Business_Understanding': ('dashboard', 'leer'),
        '02_Data_Understanding': ('dashboard', 'leer'),
        '03_Data_Preparation': ('entrenamiento', 'leer'),
        '04_Modeling': ('entrenamiento', 'leer'),
        '05_Evaluation': ('evaluacion', 'leer'),
        '06_Deployment': ('prediccion', 'leer'),
        'reports': ('reportes', 'ejecutar'),
        'admin': ('admin', 'leer'),
    }

    resource, action = page_permissions.get(page, ('dashboard', 'leer'))
    if not has_permission(resource, action):
        st.warning('No tiene permisos para acceder a esta página. Se redirigirá al dashboard.')
        st.session_state.current_page = 'dashboard'
        st.rerun()


def render_page():
    page = st.session_state.get('current_page', 'login')
    route_guard(page)
    if page == 'login':
        from ui.pages.login import render_login
        render_login()
        return

    try:
        if page == 'dashboard':
            require_permission('dashboard', 'leer')
            from ui.pages.dashboard import render_dashboard
            render_dashboard()
        elif page == '01_Business_Understanding':
            require_permission('dashboard', 'leer')
            module = importlib.import_module('ui.pages.01_Business_Understanding')
            module.render_business_understanding()
        elif page == '02_Data_Understanding':
            require_permission('dashboard', 'leer')
            module = importlib.import_module('ui.pages.02_Data_Understanding')
            module.render_data_understanding()
        elif page == '03_Data_Preparation':
            require_permission('entrenamiento', 'leer')
            module = importlib.import_module('ui.pages.03_Data_Preparation')
            module.render_data_preparation()
        elif page == '04_Modeling':
            require_permission('entrenamiento', 'leer')
            module = importlib.import_module('ui.pages.04_Modeling')
            module.render_modeling()
        elif page == '05_Evaluation':
            require_permission('evaluacion', 'leer')
            module = importlib.import_module('ui.pages.05_Evaluation')
            module.render_evaluation()
        elif page == '06_Deployment':
            require_permission('prediccion', 'leer')
            module = importlib.import_module('ui.pages.06_Deployment')
            module.render_deployment()
        elif page == 'reports':
            require_permission('reportes', 'ejecutar')
            from ui.pages.reports import render_reports
            render_reports()
        elif page == 'admin':
            require_permission('admin', 'leer')
            from ui.pages.admin import render_admin
            render_admin()
        else:
            st.error(f'Página no encontrada: {page}')
    except Exception as exc:
        st.error(f'Error al cargar la página: {exc}')


def main():
    init_session_state()
    try:
        db_pool.initialize()
    except Exception:
        st.warning('La base de datos no está disponible. Puede continuar con una sesión local o configurar PostgreSQL.')
    render_sidebar()
    render_page()


if __name__ == '__main__':
    main()