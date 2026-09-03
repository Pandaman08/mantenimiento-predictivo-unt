import streamlit as st


def render_data_preparation():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">🧹 Fase 3: Preparación de Datos</h2></div>', unsafe_allow_html=True)
    st.markdown('### Pipeline propuesto')
    st.graphviz_chart('''
    digraph pipeline {
        rankdir=LR;
        raw [label="Lecturas brutas"];
        clean [label="Limpieza\nNulos y duplicados"];
        features [label="Feature engineering\nRolling stats"];
        scale [label="Escalado\nStandarization"];
        target [label="Etiquetado\nFalla en 24h"];
        model [label="Modelado"];
        raw -> clean -> features -> scale -> target -> model;
    }
    ''')
    st.download_button('Descargar dataset procesado', b'No hay dataset generado en este entorno.', file_name='dataset_procesado.csv', mime='text/csv')
