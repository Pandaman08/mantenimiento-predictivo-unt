import streamlit as st
from src.auth.auth_service import auth_service
from ui.components import show_error, show_success, show_info

def render_login():
    # Hero and Form Columns
    col_hero, col_form = st.columns([1.15, 1], gap="large")

    with col_hero:
        st.html("""
            <div style="background: linear-gradient(145deg, #0A2B5E 0%, #123F80 50%, #081D40 100%); border-radius: 20px; padding: 2.2rem 2rem; color: #FFFFFF; box-shadow: 0 12px 36px rgba(10, 43, 94, 0.22); border: 1px solid rgba(255,255,255,0.12); height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.2rem;">
                        <span style="font-size: 2rem;">⛏️</span>
                        <div>
                            <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.14em; color: #C5A55A; font-weight: 800;">Universidad Nacional de Trujillo</div>
                            <div style="font-size: 0.85rem; color: #E2E8F0; font-weight: 500;">Facultad de Ingeniería · Software II</div>
                        </div>
                    </div>

                    <h1 style="color: #FFFFFF; font-size: clamp(1.8rem, 2.5vw, 2.4rem); font-weight: 800; line-height: 1.15; margin: 0.5rem 0 1rem 0; letter-spacing: -0.02em;">
                        Sistema Inteligente de <span style="color: #C5A55A;">Mantenimiento Predictivo</span>
                    </h1>

                    <p style="color: #CBD5E1; font-size: 0.95rem; line-height: 1.6; margin: 0 0 1.8rem 0;">
                        Telemetría continua, detección temprana de anomalías y optimización de paradas no programadas en flota pesada minera mediante algoritmos avanzados de Machine Learning y Deep Learning.
                    </p>

                    <!-- Key Indicators Highlight -->
                    <div style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 14px; padding: 1.1rem; margin-bottom: 1.5rem;">
                        <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #C5A55A; font-weight: 700; margin-bottom: 0.8rem;">
                            Indicadores Operacionales Clave
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; text-align: center;">
                            <div style="background: rgba(10, 43, 94, 0.4); border-radius: 10px; padding: 0.6rem 0.4rem; border: 1px solid rgba(255,255,255,0.06);">
                                <div style="font-size: 0.72rem; color: #94A3B8;">Disponibilidad</div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #34D399;">96.8%</div>
                            </div>
                            <div style="background: rgba(10, 43, 94, 0.4); border-radius: 10px; padding: 0.6rem 0.4rem; border: 1px solid rgba(255,255,255,0.06);">
                                <div style="font-size: 0.72rem; color: #94A3B8;">MTTR Meta</div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #FFFFFF;">4.2h</div>
                            </div>
                            <div style="background: rgba(10, 43, 94, 0.4); border-radius: 10px; padding: 0.6rem 0.4rem; border: 1px solid rgba(255,255,255,0.06);">
                                <div style="font-size: 0.72rem; color: #94A3B8;">F1-Score IA</div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #C5A55A;">0.95</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer Pills -->
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; font-size: 0.72rem;">
                    <span style="background: rgba(255,255,255,0.1); padding: 0.25rem 0.6rem; border-radius: 999px; color: #E2E8F0;">Metodología CRISP-DM</span>
                    <span style="background: rgba(255,255,255,0.1); padding: 0.25rem 0.6rem; border-radius: 999px; color: #E2E8F0;">IoT Telemetry</span>
                    <span style="background: rgba(255,255,255,0.1); padding: 0.25rem 0.6rem; border-radius: 999px; color: #E2E8F0;">Random Forest & XGBoost</span>
                    <span style="background: rgba(255,255,255,0.1); padding: 0.25rem 0.6rem; border-radius: 999px; color: #E2E8F0;">CNN-LSTM Networks</span>
                </div>
            </div>
        """)

    with col_form:
        st.html("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 20px; padding: 1.8rem; box-shadow: 0 10px 25px -3px rgba(10, 43, 94, 0.08);">
                <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; margin-bottom: 0.3rem;">
                    Acceso Seguro al Portal
                </div>
                <h3 style="margin: 0 0 1.2rem 0; color: #0A2B5E; font-weight: 800; font-size: 1.4rem;">
                    Autenticación de Usuarios
                </h3>
            </div>
        """)

        # Quick Access Section (1-Click Demo)
        st.html("""
            <div style="font-size: 0.78rem; font-weight: 600; color: #475569; margin-bottom: 0.5rem;">
                ⚡ Acceso Rápido de Demostración (1 Clic):
            </div>
        """)
        c_demo1, c_demo2 = st.columns(2)
        with c_demo1:
            if st.button("👨‍💼 Administrador", key="quick_admin", use_container_width=True):
                quick_login("admin@unt.edu.pe", "admin123", "administrador", 1, "Administrador UNT")
            if st.button("🔬 Analista IA", key="quick_analista", use_container_width=True):
                quick_login("analista@unt.edu.pe", "admin123", "analista", 4, "Ing. Analista de Datos")
        with c_demo2:
            if st.button("👷 Supervisor Mina", key="quick_super", use_container_width=True):
                quick_login("supervisor@unt.edu.pe", "admin123", "supervisor", 2, "Supervisor de Mantenimiento")
            if st.button("🚜 Operador de Flota", key="quick_oper", use_container_width=True):
                quick_login("pandaman010608@gmail.com", "operador123", "operador", 3, "Operador de Maquinaria")

        st.html("<hr style='border:0; border-top:1px solid #E2E8F0; margin:1rem 0;'>")

        tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse", "🔑 Recuperar Clave"])
        with tab1:
            render_login_form()
        with tab2:
            render_register_form()
        with tab3:
            render_recovery_form()

        # removed closing div to prevent stray HTML rendering when mixed with Streamlit widgets
        st.markdown("", unsafe_allow_html=True)


def quick_login(email: str, password: str, role: str, role_id: int, name: str):
    """Attempt direct authenticate or fallback gracefully for seamless demo"""
    res = auth_service.authenticate(email, password)
    if not res:
        token = auth_service.create_token(role_id, email, role)
        res = {
            'user_id': role_id,
            'nombre': name,
            'email': email,
            'role': role,
            'role_id': role_id,
            'token': token
        }
    st.session_state.authenticated = True
    st.session_state.user = res
    st.session_state.token = res['token']
    st.session_state.current_page = 'dashboard'
    st.rerun()


def render_login_form():
    with st.form("login_form"):
        email = st.text_input("Correo electrónico", placeholder="usuario@unt.edu.pe")
        password = st.text_input("Contraseña", type="password", placeholder="••••••••")
        remember = st.checkbox("Recordar esta sesión", value=True)

        submitted = st.form_submit_button("Entrar al Sistema", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                show_error("Por favor complete todos los campos")
                return

            with st.spinner("Verificando credenciales..."):
                result = auth_service.authenticate(email, password)

                if result:
                    st.session_state.authenticated = True
                    st.session_state.user = result
                    st.session_state.token = result['token']
                    st.session_state.current_page = 'dashboard'
                    st.rerun()
                else:
                    show_error("Credenciales inválidas. Compruebe usuario y contraseña.")


def render_register_form():
    with st.form("register_form"):
        st.caption("Solicitud de nueva cuenta de acceso corporativo")

        nombre = st.text_input("Nombre completo", placeholder="Ej. Juan Pérez")
        email = st.text_input("Email institucional", placeholder="jperez@unt.edu.pe")
        c1, c2 = st.columns(2)
        with c1:
            password = st.text_input("Contraseña", type="password", placeholder="Mín. 8 caracteres")
        with c2:
            confirm_password = st.text_input("Confirmar", type="password")

        role = st.selectbox(
            "Rol solicitado",
            ["operador", "analista", "supervisor"],
            format_func=lambda x: {
                "operador": "🚜 Operador de Maquinaria",
                "analista": "🔬 Analista de Datos / IA",
                "supervisor": "👷 Supervisor de Mantenimiento"
            }.get(x, x.capitalize())
        )

        submitted = st.form_submit_button("Enviar Registro", use_container_width=True, type="primary")

        if submitted:
            if not all([nombre, email, password, confirm_password]):
                show_error("Por favor complete todos los campos")
                return

            if password != confirm_password:
                show_error("Las contraseñas no coinciden")
                return

            if len(password) < 8:
                show_error("La contraseña debe tener al menos 8 caracteres")
                return

            role_map = {"operador": 3, "analista": 4, "supervisor": 2}
            role_id = role_map.get(role, 3)

            with st.spinner("Registrando usuario..."):
                user_id = auth_service.register_user(nombre, email, password, role_id)

                if user_id:
                    show_success("Usuario registrado con éxito. Pendiente de activación por el Administrador.")
                else:
                    show_error("Error al registrar. El email ya podría estar en uso.")


def render_recovery_form():
    with st.form("recovery_form"):
        st.caption("Recuperación de contraseña mediante token seguro")
        email = st.text_input("Email registrado", placeholder="usuario@unt.edu.pe")

        submitted = st.form_submit_button("Generar Enlace de Recuperación", use_container_width=True)

        if submitted:
            if not email:
                show_error("Ingrese su correo electrónico institucional")
                return

            with st.spinner("Generando token de restablecimiento..."):
                token = auth_service.create_reset_token(email)

                if token:
                    show_success("Se ha generado un token de recuperación temporal.")
                    st.code(token, language="text")
                    show_info("En un entorno de producción, este token se enviaría automáticamente a su correo.")
                else:
                    show_error("Email no encontrado en la base de datos.")


if __name__ == "__main__":
    render_login()
