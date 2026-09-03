import streamlit as st
import pandas as pd


def render_data_understanding():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">📈 Fase 2: Comprensión de Datos</h2></div>', unsafe_allow_html=True)
    st.markdown('### Descripción de variables')
    variables = [
        ('temperatura', 'Temperatura de operación del equipo; su aumento sostenido indica calentamiento anómalo.'),
        ('presion_aceite', 'Presión del aceite lubricante; variaciones repentinas indican drenaje o desgaste.'),
        ('rpm', 'Velocidad de rotación del sistema; afecta la carga y el desgaste mecánico.'),
        ('vibracion', 'Nivel de vibración; indicador clave de desalineación, falta de balance o fallas estructurales.'),
        ('horas_operacion', 'Horas acumuladas de trabajo; útil para estimar desgaste progresivo.'),
    ]
    for name, desc in variables:
        st.markdown(f'- **{name}**: {desc}')

    st.markdown('---')
    st.subheader('Resumen de calidad de datos')
    sample = pd.DataFrame({
        'Variable': ['temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion'],
        'Nulos': [2.1, 3.8, 1.1, 2.7, 0.5],
        'Outliers': [4.5, 3.3, 5.2, 7.1, 2.0],
    })
    st.dataframe(sample, use_container_width=True)
