import streamlit as st


def render_deployment():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">🚀 Fase 6: Despliegue</h2></div>', unsafe_allow_html=True)
    st.subheader('Predicción en tiempo real')
    temperature = st.slider('Temperatura (°C)', 50, 130, 93)
    pressure = st.slider('Presión de aceite (PSI)', 80, 280, 180)
    rpm = st.slider('RPM', 1000, 2600, 1800)
    vibration = st.slider('Vibración (mm/s)', 0.5, 10.0, 3.0)
    if st.button('Predecir falla', type='primary'):
        score = (temperature / 150) + (pressure / 300) + (rpm / 2600) + (vibration / 10)
        label = 'Falla probable' if score > 1.15 else 'Operación estable'
        st.success(f'Resultado: {label} (confianza estimada: {min(score * 100 / 1.8, 99.9):.1f}%)')
