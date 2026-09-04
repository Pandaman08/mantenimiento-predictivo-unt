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
                --unt-muted: #475569;
                --unt-border: #CBD5E1;
                --unt-success: #059669;
                --unt-warning: #D97706;
                --unt-danger: #DC2626;
                --unt-info: #0284C7;
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 25px -3px rgba(10, 43, 94, 0.08), 0 4px 6px -2px rgba(10, 43, 94, 0.04);
            }

            html, body, [class*='st'] {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            html, body, [class*='stApp'] {
                background: #F8FAFC !important;
                color: #0F172A !important;
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
                border: 1px solid #CBD5E1;
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
                color: #0A2B5E !important;
                letter-spacing: -0.01em;
            }

            .unt-top-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.75rem;
                font-weight: 700;
                background: #ECFDF5;
                color: #065F46 !important;
                border: 1px solid #6EE7B7;
            }

            /* Industrial Cards */
            .unt-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.25rem;
                border: 1px solid #CBD5E1;
                box-shadow: var(--shadow-sm);
                transition: all 0.2s ease;
                margin-bottom: 1rem;
                color: #0F172A;
            }

            .unt-card:hover {
                box-shadow: var(--shadow-md);
                border-color: #94A3B8;
            }

            /* KPI Cards */
            .unt-kpi-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 1.15rem 1.25rem;
                border: 1px solid #CBD5E1;
                box-shadow: var(--shadow-sm);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                position: relative;
                overflow: hidden;
            }

            .unt-kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
                border-color: #94A3B8;
            }

            .unt-kpi-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: #0A2B5E;
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
                border: 1px solid #CBD5E1;
                box-shadow: var(--shadow-sm);
                transition: all 0.2s ease;
                color: #0F172A;
            }

            .unt-machine-card:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
            }

            /* Status Pills with Maximum Contrast */
            .status-pill-success {
                background: #ECFDF5 !important;
                color: #065F46 !important;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 800;
                border: 1px solid #6EE7B7;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .status-pill-warning {
                background: #FFFBEB !important;
                color: #78350F !important;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 800;
                border: 1px solid #FCD34D;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .status-pill-danger {
                background: #FEF2F2 !important;
                color: #7F1D1D !important;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.72rem;
                font-weight: 800;
                border: 1px solid #FCA5A5;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            /* Role Badges - High Contrast */
            .role-badge {
                display: inline-block;
                padding: 0.25rem 0.65rem;
                border-radius: 999px;
                font-size: 0.7rem;
                font-weight: 800 !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .role-administrador { background: #EEF2FF !important; color: #312E81 !important; border: 1px solid #A5B4FC !important; }
            .role-supervisor { background: #FEF3C7 !important; color: #78350F !important; border: 1px solid #FDE68A !important; }
            .role-analista { background: #E0F2FE !important; color: #0C4A6E !important; border: 1px solid #7DD3FC !important; }
            .role-operador { background: #D1FAE5 !important; color: #065F46 !important; border: 1px solid #6EE7B7 !important; }

            /* CRISP-DM Stepper */
            .unt-stepper-container {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
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
                background: linear-gradient(135deg, #0A2B5E 0%, #123F80 100%) !important;
                color: #FFFFFF !important;
                box-shadow: 0 4px 12px rgba(10, 43, 94, 0.25);
            }

            .step-item.active .step-badge {
                background: #C5A55A !important;
                color: #0A2B5E !important;
                font-weight: 800 !important;
            }

            .step-item.active .step-title {
                color: #FFFFFF !important;
                font-weight: 700 !important;
            }

            .step-item.completed {
                background: #F0FDF4 !important;
                border-color: #BBF7D0 !important;
                color: #166534 !important;
            }

            .step-item.completed .step-badge {
                background: #DCFCE7 !important;
                color: #166534 !important;
                font-weight: 800 !important;
            }

            .step-item.completed .step-title {
                color: #166534 !important;
                font-weight: 700 !important;
            }

            .step-item.upcoming {
                background: #F1F5F9 !important;
                border-color: #CBD5E1 !important;
                color: #475569 !important;
            }

            .step-item.upcoming .step-badge {
                background: #E2E8F0 !important;
                color: #475569 !important;
                font-weight: 700 !important;
            }

            .step-item.upcoming .step-title {
                color: #475569 !important;
                font-weight: 600 !important;
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

            /* Streamlit Native Elements High Contrast Overrides */
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
                background: linear-gradient(135deg, #0A2B5E 0%, #123F80 100%) !important;
                color: #FFFFFF !important;
                border: 0 !important;
                font-weight: 700 !important;
            }

            .stButton > button[kind='secondary'] {
                background: #FFFFFF !important;
                color: #0A2B5E !important;
                border: 1px solid #CBD5E1 !important;
                font-weight: 600 !important;
            }

            .stButton > button[kind='secondary']:hover {
                border-color: #0A2B5E !important;
                background: #F8FAFC !important;
            }

            /* Streamlit Alerts (st.info, st.success, st.warning, st.error) FIX */
            [data-testid="stAlert"], .stAlert {
                border-radius: 12px !important;
                padding: 0.85rem 1.15rem !important;
            }

            [data-testid="stAlert"] [data-testid="stMarkdownContainer"],
            [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
            [data-testid="stAlert"] [data-testid="stMarkdownContainer"] strong,
            [data-testid="stAlert"] [data-testid="stMarkdownContainer"] code {
                font-weight: 600 !important;
            }

            /* st.info Callout Box Fix (Celeste with White Text Fix) */
            [data-testid="stAlert"]:has(div[kind="info"]),
            div[kind="info"],
            .stAlert:has(.st-emotion-cache-1wivap2) {
                background-color: #E0F2FE !important;
                border: 1px solid #38BDF8 !important;
            }
            [data-testid="stAlert"]:has(div[kind="info"]) [data-testid="stMarkdownContainer"] p,
            [data-testid="stAlert"]:has(div[kind="info"]) [data-testid="stMarkdownContainer"] span,
            [data-testid="stAlert"]:has(div[kind="info"]) [data-testid="stMarkdownContainer"] strong,
            div[kind="info"] p, div[kind="info"] span, div[kind="info"] strong {
                color: #0C4A6E !important;
            }

            /* st.success Callout Box Fix */
            [data-testid="stAlert"]:has(div[kind="success"]),
            div[kind="success"] {
                background-color: #ECFDF5 !important;
                border: 1px solid #34D399 !important;
            }
            [data-testid="stAlert"]:has(div[kind="success"]) [data-testid="stMarkdownContainer"] p,
            [data-testid="stAlert"]:has(div[kind="success"]) [data-testid="stMarkdownContainer"] span,
            [data-testid="stAlert"]:has(div[kind="success"]) [data-testid="stMarkdownContainer"] strong,
            div[kind="success"] p, div[kind="success"] span, div[kind="success"] strong {
                color: #065F46 !important;
            }

            /* st.warning Callout Box Fix */
            [data-testid="stAlert"]:has(div[kind="warning"]),
            div[kind="warning"] {
                background-color: #FFFBEB !important;
                border: 1px solid #FBBF24 !important;
            }
            [data-testid="stAlert"]:has(div[kind="warning"]) [data-testid="stMarkdownContainer"] p,
            [data-testid="stAlert"]:has(div[kind="warning"]) [data-testid="stMarkdownContainer"] span,
            [data-testid="stAlert"]:has(div[kind="warning"]) [data-testid="stMarkdownContainer"] strong,
            div[kind="warning"] p, div[kind="warning"] span, div[kind="warning"] strong {
                color: #78350F !important;
            }

            /* st.error Callout Box Fix */
            [data-testid="stAlert"]:has(div[kind="error"]),
            div[kind="error"] {
                background-color: #FEF2F2 !important;
                border: 1px solid #F87171 !important;
            }
            [data-testid="stAlert"]:has(div[kind="error"]) [data-testid="stMarkdownContainer"] p,
            [data-testid="stAlert"]:has(div[kind="error"]) [data-testid="stMarkdownContainer"] span,
            [data-testid="stAlert"]:has(div[kind="error"]) [data-testid="stMarkdownContainer"] strong,
            div[kind="error"] p, div[kind="error"] span, div[kind="error"] strong {
                color: #7F1D1D !important;
            }

            /* Sidebar Styling - Maximum Legibility & No Text Clipping */
            [data-testid='stSidebar'] {
                background: #0A1E3F !important;
                border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            }

            [data-testid='stSidebar'] [data-testid='stVerticalBlock'] {
                gap: 0.35rem;
            }

            .sidebar-nav-header {
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.09em;
                color: #CBD5E1 !important;
                font-weight: 800;
                padding: 0.7rem 0.4rem 0.25rem 0.4rem;
                margin-top: 0.4rem;
            }

            [data-testid='stSidebar'] .stButton {
                width: 100% !important;
                margin-bottom: 0.15rem !important;
            }

            [data-testid='stSidebar'] .stButton > button {
                width: 100% !important;
                min-height: 42px !important;
                height: auto !important;
                white-space: normal !important;
                word-break: break-word !important;
                text-align: left !important;
                justify-content: flex-start !important;
                align-items: center !important;
                padding: 0.55rem 0.85rem !important;
                border-radius: 10px !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                line-height: 1.35 !important;
                transition: all 0.15s ease !important;
            }

            /* Secondary (Inactive) Sidebar Nav Buttons */
            [data-testid='stSidebar'] .stButton > button[kind='secondary'],
            [data-testid='stSidebar'] .stButton > button:not([kind='primary']) {
                background: rgba(255, 255, 255, 0.05) !important;
                color: #E2E8F0 !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
            }

            [data-testid='stSidebar'] .stButton > button[kind='secondary'] *,
            [data-testid='stSidebar'] .stButton > button:not([kind='primary']) * {
                color: #E2E8F0 !important;
            }

            [data-testid='stSidebar'] .stButton > button[kind='secondary']:hover,
            [data-testid='stSidebar'] .stButton > button:not([kind='primary']):hover {
                background: rgba(255, 255, 255, 0.14) !important;
                color: #FFFFFF !important;
                border-color: rgba(255, 255, 255, 0.25) !important;
            }

            [data-testid='stSidebar'] .stButton > button[kind='secondary']:hover *,
            [data-testid='stSidebar'] .stButton > button:not([kind='primary']):hover * {
                color: #FFFFFF !important;
            }

            /* Primary (Active / Selected) Sidebar Nav Buttons */
            [data-testid='stSidebar'] .stButton > button[kind='primary'] {
                background: linear-gradient(135deg, #C5A55A 0%, #B59345 100%) !important;
                color: #0A2B5E !important;
                border: 0 !important;
                font-weight: 800 !important;
                box-shadow: 0 4px 14px rgba(197, 165, 90, 0.35) !important;
            }

            [data-testid='stSidebar'] .stButton > button[kind='primary'] * {
                color: #0A2B5E !important;
                font-weight: 800 !important;
            }

            /* Metrics High Contrast */
            [data-testid="stMetricValue"] {
                color: #0A2B5E !important;
                font-weight: 800 !important;
            }
            [data-testid="stMetricLabel"] {
                color: #475569 !important;
                font-weight: 600 !important;
            }

            /* Tabs High Contrast */
            [data-baseweb="tab-list"] {
                background-color: transparent !important;
                gap: 0.4rem !important;
                border-bottom: 2px solid #E2E8F0 !important;
            }
            [data-baseweb="tab"] {
                color: #64748B !important;
                font-weight: 600 !important;
                border-radius: 8px 8px 0 0 !important;
                padding: 0.6rem 1.1rem !important;
                background: transparent !important;
            }
            [data-baseweb="tab"][aria-selected="true"] {
                color: #0A2B5E !important;
                background: #FFFFFF !important;
                font-weight: 800 !important;
                border-bottom: 3px solid #0A2B5E !important;
            }

            /* Multiselect Tags & Selectboxes */
            span[data-baseweb="tag"] {
                background-color: #E0F2FE !important;
                color: #0C4A6E !important;
                border: 1px solid #7DD3FC !important;
                font-weight: 700 !important;
            }

            /* Dataframes & Tables */
            [data-testid='stDataFrame'] {
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #CBD5E1;
                background: #FFFFFF !important;
            }

            /* Expanders */
            [data-testid="stExpander"] {
                background: #FFFFFF !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 12px !important;
            }
            [data-testid="stExpander"] summary span {
                color: #0A2B5E !important;
                font-weight: 700 !important;
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
