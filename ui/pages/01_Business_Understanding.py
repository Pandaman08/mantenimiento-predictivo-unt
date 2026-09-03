import streamlit as st


def render_business_understanding():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">🏢 Fase 1: Comprensión del Negocio</h2></div>', unsafe_allow_html=True)
    st.markdown('### Objetivos estratégicos')
    col1, col2, col3 = st.columns(3)
    goals = [
        ('Reducción MTTR', '-20%', 'Tiempo medio de reparación'),
        ('Disponibilidad', '+5%', 'Disponibilidad del sistema'),
        ('Costos', '-15%', 'Costos de mantenimiento'),
    ]
    for i, (label, target, desc) in enumerate(goals):
        with [col1, col2, col3][i]:
            st.markdown(f"""
            <div class='unt-card'>
                <h4>{label}</h4>
                <div style='font-size:1.8rem; font-weight:800; color:#0A2B5E;'>{target}</div>
                <div style='color:#4a4a4a;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('---')
    st.subheader('Estado actual vs meta')
    current_metrics = [
        ('MTTR actual', 12.5, 'h', 'Objetivo 10.0 h'),
        ('Disponibilidad actual', 94.0, '%', 'Objetivo 99.0%'),
        ('Costo anual', 640000, 'S/', 'Objetivo 544000 S/'),
    ]
    for label, value, unit, target_text in current_metrics:
        st.metric(label=label, value=f'{value} {unit}', delta=target_text)
