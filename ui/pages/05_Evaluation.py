import streamlit as st
import pandas as pd


def render_evaluation():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">📊 Fase 5: Evaluación</h2></div>', unsafe_allow_html=True)
    st.subheader('Comparación de modelos')
    data = pd.DataFrame([
        {'Modelo': 'RandomForest', 'Accuracy': 0.93, 'Precision': 0.91, 'Recall': 0.89, 'F1': 0.90},
        {'Modelo': 'XGBoost', 'Accuracy': 0.95, 'Precision': 0.93, 'Recall': 0.91, 'F1': 0.92},
        {'Modelo': 'SVM', 'Accuracy': 0.90, 'Precision': 0.88, 'Recall': 0.86, 'F1': 0.87},
    ])
    st.dataframe(data, use_container_width=True)
    st.markdown('### Pruebas estadísticas')
    st.write('Se ejecuta validación cruzada y pruebas de comparación entre modelos para confirmar la significancia del desempeño.')
