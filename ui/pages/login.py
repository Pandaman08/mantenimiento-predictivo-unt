import streamlit as st
from src.auth.auth_service import auth_service
from ui.components import show_error, show_success, show_info

def render_login():
    st.markdown(
        """
        <div class="login-shell">
            <div style="display:flex; flex-wrap:wrap; gap:1.25rem; align-items:stretch;">
                <div class="login-hero" style="flex:1.15; min-width:260px;">
                    <div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.12em; opacity:0.85; margin-bottom:0.75rem;">Universidad Nacional de Trujillo</div>
                    <h1>⛏️ Mantenimiento Predictivo</h1>
                    <p style="margin:0.75rem 0 0; line-height:1.6; opacity:0.9;">Plataforma inteligente para monitorizar equipos, anticipar fallas y optimizar decisiones de mantenimiento.</p>
                    <div style="margin-top:1.3rem; padding:0.8rem 1rem; border-radius:16px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.12);">
                        <strong>Indicadores clave</strong>
                        <div style="margin-top:0.75rem; display:grid; grid-template-columns:repeat(2, minmax(110px, 1fr)); gap:0.6rem;">
                            <div><div style="font-size:0.7rem; opacity:0.75;">Disponibilidad</div><div style="font-size:1.25rem; font-weight:700;">96.8%</div></div>
                            <div><div style="font-size:0.7rem; opacity:0.75;">MTTR</div><div style="font-size:1.25rem; font-weight:700;">5.2h</div></div>
                        </div>
                    </div>
                </div>
                <div class="login-panel" style="flex:1; min-width:300px;">
                    <div style="font-size:0.75rem; color:#52657d; text-transform:uppercase; letter-spacing:0.1em; font-weight:700; margin-bottom:0.7rem;">Acceso al sistema</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse", "🔑 Recuperar Contraseña"])
        with tab1:
            render_login_form()
        with tab2:
            render_register_form()
        with tab3:
            render_recovery_form()

    st.markdown(
        """
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_login_form():
    with st.form("login_form"):
        st.markdown("### Iniciar Sesión")
        email = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password = st.text_input("Contraseña", type="password", placeholder="********")
        remember = st.checkbox("Recordarme")

        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                show_error("Por favor complete todos los campos")
                return

            with st.spinner("Autenticando..."):
                result = auth_service.authenticate(email, password)

                if result:
                    st.session_state.authenticated = True
                    st.session_state.user = result
                    st.session_state.token = result['token']
                    st.session_state.current_page = 'dashboard'
                    show_success("¡Bienvenido!")
                    st.rerun()
                else:
                    show_error("Credenciales inválidas")

def render_register_form():
    with st.form("register_form"):
        st.markdown("### Registro de Usuario")
        st.info("Nota: El administrador debe aprobar tu cuenta")

        nombre = st.text_input("Nombre completo")
        email = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password = st.text_input("Contraseña", type="password", placeholder="Mínimo 8 caracteres")
        confirm_password = st.text_input("Confirmar contraseña", type="password")

        # Role selection (only for admins creating users, but show for demo)
        role = st.selectbox("Rol solicitado",
                           ["operador", "analista", "supervisor"],
                           format_func=lambda x: x.capitalize())

        submitted = st.form_submit_button("Registrarse", use_container_width=True)

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

            # Map role to role_id
            role_map = {"operador": 3, "analista": 4, "supervisor": 2}
            role_id = role_map.get(role, 3)

            with st.spinner("Registrando..."):
                user_id = auth_service.register_user(nombre, email, password, role_id)

                if user_id:
                    show_success("Usuario registrado. Pendiente de activación por administrador.")
                else:
                    show_error("Error al registrar. El email ya puede estar en uso.")

def render_recovery_form():
    with st.form("recovery_form"):
        st.markdown("### Recuperar Contraseña")
        email = st.text_input("Email registrado", placeholder="usuario@ejemplo.com")

        submitted = st.form_submit_button("Enviar enlace de recuperación", use_container_width=True)

        if submitted:
            if not email:
                show_error("Ingrese su email")
                return

            with st.spinner("Generando token..."):
                token = auth_service.create_reset_token(email)

                if token:
                    show_success("Se ha generado un token de recuperación.")
                    show_info(f"Token (simulado): {token[:50]}...")
                    st.code(token, language="text")
                else:
                    show_error("Email no encontrado o error en el sistema")

if __name__ == "__main__":
    render_login()