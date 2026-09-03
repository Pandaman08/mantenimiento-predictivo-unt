import importlib
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.auth.auth_service import auth_service
from src.db.connection import db_pool
from utils.helpers import sanitize_text

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
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

            :root {
                --unt-primary: #0A2B5E;
                --unt-primary-2: #123F80;
                --unt-gold: #C5A55A;
                --unt-gold-hover: #B59345;
                --unt-bg: #F8FAFC;
                --unt-surface: #FFFFFF;
                --unt-text: #0F172A;
                --unt-muted: #64748B;
                --unt-border: #E2E8F0;
                --unt-success: #10B981;
                --unt-warning: #F59E0B;
                --unt-danger: #EF4444;
                --unt-info: #0284C7;
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 25px -3px rgba(10, 43, 94, 0.08), 0 4px 6px -2px rgba(10, 43, 94, 0.04);
            }

            html, body, [class*='st'] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            html, body, [class*='stApp'] {
                background: #F8FAFC;
                color: var(--unt-text);
            }

            .block-container {
                padding-top: 1rem;
                padding-bottom: 2.5rem;
                max-width: 1400px;
            }

            /* Custom Top Bar */
            .unt-top-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #FFFFFF;
                border: 1px solid var(--unt-border);
                border-radius: 14px;
                padding: 0.75rem 1.25rem;
                margin-bottom: 1.25rem;
                box-shadow: var(--shadow-sm);
            }

            .unt-top-title {
                display: flex;
                align-items: center;
                gap: 0.75rem;
            }

            .unt-top-title h2 {
                margin: 0;
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--unt-primary);
                letter-spacing: -0.01em;
            }

            .unt-top-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 600;
                background: #ECFDF5;
                color: #065F46;
                border: 1px solid #A7F3D0;
            }

            /* Industrial Cards */
            .unt-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.25rem;
                border: 1px solid var(--unt-border);
                box-shadow: var(--shadow-sm);
                transition: all 0.2s ease;
                margin-bottom: 1rem;
            }

            .unt-card:hover {
                box-shadow: var(--shadow-md);
                border-color: #CBD5E1;
            }

            /* KPI Cards */
            .unt-kpi-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.15rem 1.25rem;
                border: 1px solid var(--unt-border);
                box-shadow: var(--shadow-sm);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                position: relative;
                overflow: hidden;
            }

            .unt-kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
                border-color: #CBD5E1;
            }

            .unt-kpi-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: var(--unt-primary);
            }

            .unt-kpi-icon {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                height: 36px;
                border-radius: 10px;
                background: #F1F5F9;
                font-size: 1.1rem;
            }

            /* Machine Cards */
            .unt-machine-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.1rem;
                border: 1px solid var(--unt-border);
                box-shadow: var(--shadow-sm);
                transition: all 0.2s ease;
            }

            .unt-machine-card:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
            }

            /* Status Pills */
            .status-pill-success {
                background: #ECFDF5;
                color: #065F46;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                border: 1px solid #A7F3D0;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .status-pill-warning {
                background: #FFFBEB;
                color: #92400E;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                border: 1px solid #FDE68A;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .status-pill-danger {
                background: #FEF2F2;
                color: #991B1B;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 700;
                border: 1px solid #FECACA;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            /* Role Badges */
            .role-badge {
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .role-administrador { background: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE; }
            .role-supervisor { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
            .role-analista { background: #E0F2FE; color: #075985; border: 1px solid #BAE6FD; }
            .role-operador { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }

            /* CRISP-DM Stepper */
            .unt-stepper-container {
                background: #FFFFFF;
                border: 1px solid var(--unt-border);
                border-radius: 14px;
                padding: 1rem 1.25rem;
                margin-bottom: 1.25rem;
                box-shadow: var(--shadow-sm);
            }

            .step-item {
                border-radius: 10px;
                padding: 0.6rem 0.5rem;
                text-align: center;
                transition: all 0.2s ease;
                border: 1px solid transparent;
            }

            .step-item.active {
                background: linear-gradient(135deg, var(--unt-primary) 0%, var(--unt-primary-2) 100%);
                color: #FFFFFF !important;
                box-shadow: 0 4px 12px rgba(10, 43, 94, 0.25);
            }

            .step-item.active .step-badge {
                background: var(--unt-gold);
                color: #0A2B5E;
                font-weight: 800;
            }

            .step-item.active .step-title {
                color: #FFFFFF;
                font-weight: 700;
            }

            .step-item.completed {
                background: #F0FDF4;
                border-color: #DCFCE7;
                color: #166534;
            }

            .step-item.completed .step-badge {
                background: #DCFCE7;
                color: #166534;
            }

            .step-item.completed .step-title {
                color: #166534;
                font-weight: 600;
            }

            .step-item.upcoming {
                background: #F8FAFC;
                border-color: #E2E8F0;
                color: var(--unt-muted);
            }

            .step-item.upcoming .step-badge {
                background: #E2E8F0;
                color: #64748B;
            }

            .step-item.upcoming .step-title {
                color: #64748B;
            }

            .step-badge {
                display: inline-block;
                padding: 0.15rem 0.45rem;
                border-radius: 999px;
                font-size: 0.65rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
                letter-spacing: 0.04em;
            }

            .step-title {
                font-size: 0.78rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            /* Streamlit Native Elements Overrides */
            .stButton > button {
                border-radius: 10px;
                font-weight: 600;
                font-size: 0.88rem;
                padding: 0.5rem 1.1rem;
                transition: all 0.2s ease;
                box-shadow: var(--shadow-sm);
            }

            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }

            .stButton > button[kind='primary'] {
                background: linear-gradient(135deg, var(--unt-primary) 0%, var(--unt-primary-2) 100%) !important;
                color: #FFFFFF !important;
                border: 0 !important;
            }

            .stButton > button[kind='secondary'] {
                background: #FFFFFF !important;
                color: var(--unt-primary) !important;
                border: 1px solid var(--unt-border) !important;
            }

            .stButton > button[kind='secondary']:hover {
                border-color: var(--unt-primary) !important;
                background: #F8FAFC !important;
            }

            /* Sidebar Styling */
            [data-testid='stSidebar'] {
                background: #0A1E3F !important;
                border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            }

            [data-testid='stSidebar'] [data-testid='stVerticalBlock'] {
                gap: 0.4rem;
            }

            .sidebar-nav-header {
                font-size: 0.68rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #94A3B8;
                font-weight: 700;
                padding: 0.6rem 0.4rem 0.2rem 0.4rem;
                margin-top: 0.4rem;
            }

            [data-testid='stSidebar'] .stButton > button {
                background: rgba(255, 255, 255, 0.06);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 9px;
                font-size: 0.84rem;
                font-weight: 500;
                text-align: left;
                justify-content: flex-start;
                padding: 0.45rem 0.75rem;
                margin-bottom: 0.2rem;
            }

            [data-testid='stSidebar'] .stButton > button:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #FFFFFF;
                border-color: rgba(255, 255, 255, 0.2);
            }

            [data-testid='stSidebar'] .stButton > button[kind='primary'] {
                background: var(--unt-gold) !important;
                color: #0A2B5E !important;
                border: 0 !important;
                font-weight: 700 !important;
                box-shadow: 0 4px 12px rgba(197, 165, 90, 0.3) !important;
            }

            /* Dataframes & Tables */
            [data-testid='stDataFrame'] {
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid var(--unt-border);
            }

            /* Responsive Adjustments */
            @media (max-width: 992px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                .unt-top-bar {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 0.5rem;
                }
            }

            @media (max-width: 600px) {
                .step-item {
                    padding: 0.4rem 0.2rem;
                }
                .step-title {
                    font-size: 0.7rem;
                }
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
            'administrador': [
                'dashboard', 'modelos', 'reportes', 'usuarios', 'equipos',
                'entrenamiento', 'prediccion', 'admin', 'evaluacion', 'eda', 'negocio'
            ],
            'supervisor': [
                'dashboard', 'reportes', 'equipos', 'prediccion', 'eda', 'negocio', 'evaluacion'
            ],
            'analista': [
                'dashboard', 'modelos', 'reportes', 'entrenamiento', 'evaluacion',
                'prediccion', 'eda', 'negocio', 'equipos'
            ],
            'operador': [
                'dashboard', 'prediccion', 'equipos'
            ],
        }
        permissions = [{'resource': item, 'action': 'leer'} for item in role_permissions.get(role, [])]
        if role in ['administrador', 'analista', 'supervisor']:
            permissions.append({'resource': 'prediccion', 'action': 'ejecutar'})
            permissions.append({'resource': 'reportes', 'action': 'ejecutar'})
            permissions.append({'resource': 'entrenamiento', 'action': 'ejecutar'})
        st.session_state.permissions = permissions
    return any(p.get('resource') == resource for p in permissions)


# Categorized Navigation
NAV_GROUPS = {
    'administrador': [
        ('🚜 OPERACIONES', [
            ('dashboard', '📊 Dashboard Principal', 'dashboard'),
            ('equipos', '🚜 Flota y Sensores', 'equipos'),
            ('prediction', '🔮 Inferencia en Vivo', 'prediccion'),
            ('history', '📋 Historial Alertas', 'prediccion'),
        ]),
        ('🔬 METODOLOGÍA CRISP-DM', [
            ('01_Business_Understanding', '🎯 1. Negocio & ROI', 'negocio'),
            ('eda', '📈 2. Exploración (EDA)', 'eda'),
            ('03_Data_Preparation', '🧹 3. Pipeline de Datos', 'entrenamiento'),
            ('training', '🤖 4. Modelado ML / DL', 'entrenamiento'),
            ('evaluation', '📊 5. Evaluación Modelos', 'evaluacion'),
        ]),
        ('⚙️ GESTIÓN & REPORTES', [
            ('reports', '📄 Centro de Reportes', 'reportes'),
            ('admin', '🛡️ Administración RBAC', 'admin'),
        ]),
    ],
    'supervisor': [
        ('🚜 OPERACIONES', [
            ('dashboard', '📊 Dashboard Principal', 'dashboard'),
            ('equipos', '🚜 Flota y Sensores', 'equipos'),
            ('prediction', '🔮 Inferencia en Vivo', 'prediccion'),
            ('history', '📋 Historial Alertas', 'prediccion'),
        ]),
        ('🔬 SUPERVISIÓN ANALÍTICA', [
            ('01_Business_Understanding', '🎯 Objetivos & ROI', 'negocio'),
            ('eda', '📈 Exploración (EDA)', 'eda'),
            ('evaluation', '📊 Rendimiento Modelos', 'evaluacion'),
        ]),
        ('⚙️ GESTIÓN', [
            ('reports', '📄 Centro de Reportes', 'reportes'),
        ]),
    ],
    'analista': [
        ('🚜 OPERACIONES', [
            ('dashboard', '📊 Dashboard Principal', 'dashboard'),
            ('equipos', '🚜 Flota y Sensores', 'equipos'),
            ('prediction', '🔮 Inferencia en Vivo', 'prediccion'),
            ('history', '📋 Historial Alertas', 'prediccion'),
        ]),
        ('🔬 METODOLOGÍA CRISP-DM', [
            ('01_Business_Understanding', '🎯 1. Negocio & ROI', 'negocio'),
            ('eda', '📈 2. Exploración (EDA)', 'eda'),
            ('03_Data_Preparation', '🧹 3. Pipeline de Datos', 'entrenamiento'),
            ('training', '🤖 4. Modelado ML / DL', 'entrenamiento'),
            ('evaluation', '📊 5. Evaluación Modelos', 'evaluacion'),
        ]),
        ('⚙️ GESTIÓN', [
            ('reports', '📄 Centro de Reportes', 'reportes'),
        ]),
    ],
    'operador': [
        ('🚜 OPERACIONES DE CAMPO', [
            ('dashboard', '📊 Dashboard Operativo', 'dashboard'),
            ('equipos', '🚜 Estado de Maquinaria', 'equipos'),
            ('prediction', '🔮 Diagnóstico en Vivo', 'prediccion'),
            ('history', '📋 Registro de Alertas', 'prediccion'),
        ]),
    ],
}


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align:center; padding: 0.8rem 0 0.5rem 0;'>
                <div style='display:inline-flex; align-items:center; justify-content:center; width:48px; height:48px; border-radius:12px; background:linear-gradient(135deg, #C5A55A, #DFC382); color:#0A2B5E; font-size:1.5rem; margin-bottom:8px; box-shadow:0 4px 14px rgba(197, 165, 90, 0.35);'>
                    ⛏️
                </div>
                <h3 style='margin:0; color:#FFFFFF; font-size:1.15rem; font-weight:800; letter-spacing:-0.01em;'>UNT MINING AI</h3>
                <div style='font-size:0.75rem; color:#94A3B8; font-weight:500;'>Mantenimiento Predictivo</div>
            </div>
            <hr style='border:0; border-top:1px solid rgba(255,255,255,0.08); margin:0.8rem 0;'>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get('authenticated'):
            user = st.session_state.get('user') or {}
            role = user.get('role', 'operador')
            user_name = user.get('nombre', 'Usuario')
            user_email = user.get('email', '')
            initials = ''.join([part[0].upper() for part in user_name.split()[:2]]) if user_name else 'U'

            st.markdown(
                f"""
                <div style='background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:0.85rem; margin-bottom:1rem;'>
                    <div style='display:flex; align-items:center; gap:0.75rem;'>
                        <div style='width:36px; height:36px; border-radius:999px; background:linear-gradient(135deg, #123F80, #1E4E94); color:#FFFFFF; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.85rem; border:1px solid rgba(255,255,255,0.2);'>
                            {initials}
                        </div>
                        <div style='flex:1; min-width:0;'>
                            <div style='font-weight:700; color:#FFFFFF; font-size:0.88rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{sanitize_text(user_name)}</div>
                            <div style='font-size:0.72rem; color:#94A3B8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{sanitize_text(user_email)}</div>
                        </div>
                    </div>
                    <div style='margin-top:0.6rem; display:flex; justify-content:space-between; align-items:center;'>
                        <span class='role-badge role-{role}'>{role}</span>
                        <span style='font-size:0.7rem; color:#34D399; font-weight:600;'>● En Línea</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            groups = NAV_GROUPS.get(role, NAV_GROUPS['operador'])
            current_page = st.session_state.get('current_page', 'dashboard')

            for group_title, items in groups:
                st.markdown(f"<div class='sidebar-nav-header'>{sanitize_text(group_title)}</div>", unsafe_allow_html=True)
                for page_key, page_label, perm_resource in items:
                    if has_permission(perm_resource, 'leer'):
                        is_current = (current_page == page_key)
                        button_type = 'primary' if is_current else 'secondary'
                        if st.button(page_label, key=f'nav_{page_key}', use_container_width=True, type=button_type):
                            st.session_state.current_page = page_key
                            st.rerun()

            st.markdown("<hr style='border:0; border-top:1px solid rgba(255,255,255,0.08); margin:1rem 0 0.6rem 0;'>", unsafe_allow_html=True)
            if st.button('🚪 Cerrar Sesión', key='btn_logout', use_container_width=True):
                for key in DEFAULT_SESSION:
                    st.session_state[key] = DEFAULT_SESSION[key]
                st.session_state.current_page = 'login'
                st.rerun()
        else:
            st.markdown(
                """
                <div style='text-align:center; padding:1.5rem 0.5rem; color:#94A3B8; font-size:0.85rem;'>
                    🔒 Inicie sesión para acceder al centro de telemetría y modelos de predicción.
                </div>
                """,
                unsafe_allow_html=True
            )


def render_top_bar():
    """Top operational status bar for authenticated users"""
    if not st.session_state.get('authenticated'):
        return

    page = st.session_state.get('current_page', 'dashboard')
    page_titles = {
        'dashboard': '📊 Dashboard Ejecutivo y Telemetría',
        'equipos': '🚜 Gestión de Flota y Sensores',
        'prediction': '🔮 Inferencia y Predicción en Tiempo Real',
        'history': '📋 Historial de Diagnósticos y Alertas',
        '01_Business_Understanding': '🎯 Fase 1: Objetivos del Negocio y ROI',
        'eda': '📈 Fase 2: Exploración de Datos (EDA)',
        '03_Data_Preparation': '🧹 Fase 3: Preparación y Pipeline de Datos',
        'training': '🤖 Fase 4: Modelado y Entrenamiento de Algoritmos',
        'evaluation': '📊 Fase 5: Evaluación y Comparación de Modelos',
        'reports': '📄 Centro de Reportes Técnicos y Ejecutivos',
        'admin': '🛡️ Administración del Sistema y Auditoría',
    }
    title = page_titles.get(page, 'Mantenimiento Predictivo')

    now_str = datetime.now().strftime('%d/%m/%Y %H:%M')

    st.markdown(
        f"""
        <div class="unt-top-bar">
            <div class="unt-top-title">
                <h2>{title}</h2>
            </div>
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:0.8rem; color:#64748B; font-weight:500;">
                    🕒 {now_str}
                </span>
                <span class="unt-top-badge">
                    <span style="width:7px; height:7px; border-radius:999px; background:#10B981; display:inline-block;"></span>
                    IoT Stream Activo
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def route_guard(page: str):
    if page == 'login':
        if st.session_state.get('authenticated'):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        return

    if not st.session_state.get('authenticated'):
        st.session_state.current_page = 'login'
        st.rerun()


def render_page():
    page = st.session_state.get('current_page', 'login')
    route_guard(page)

    if page == 'login':
        from ui.pages.login import render_login
        render_login()
        return

    render_top_bar()

    try:
        if page == 'dashboard':
            from ui.pages.dashboard import render_dashboard
            render_dashboard()
        elif page == 'equipos':
            from ui.pages.equipos import render_equipos
            render_equipos()
        elif page in ['prediction', '06_Deployment']:
            from ui.pages.prediction import render_prediction
            render_prediction()
        elif page == 'history':
            from ui.pages.history import render_history
            render_history()
        elif page == '01_Business_Understanding':
            module = importlib.import_module('ui.pages.01_Business_Understanding')
            module.render_business_understanding()
        elif page in ['eda', '02_Data_Understanding']:
            from ui.pages.eda import render_eda
            render_eda()
        elif page == '03_Data_Preparation':
            module = importlib.import_module('ui.pages.03_Data_Preparation')
            module.render_data_preparation()
        elif page in ['training', '04_Modeling']:
            from ui.pages.training import render_training
            render_training()
        elif page in ['evaluation', '05_Evaluation']:
            from ui.pages.evaluation import render_evaluation
            render_evaluation()
        elif page == 'reports':
            from ui.pages.reports import render_reports
            render_reports()
        elif page == 'admin':
            from ui.pages.admin import render_admin
            render_admin()
        else:
            st.error(f'Módulo no encontrado: {page}')
    except Exception as exc:
        st.error(f'Error al cargar el módulo {page}: {exc}')


def main():
    init_session_state()
    try:
        db_pool.initialize()
    except Exception:
        pass
    render_sidebar()
    render_page()


if __name__ == '__main__':
    main()
