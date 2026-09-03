import streamlit as st


def render_modeling():
    st.markdown('<div class="unt-header"><h2 style="margin:0; color:white;">🤖 Fase 4: Modelado</h2></div>', unsafe_allow_html=True)
    st.markdown('### Entrenamiento de modelos')
    model_type = st.selectbox('Modelo', ['RandomForest', 'XGBoost', 'SVM', 'CNN-LSTM'])
    with st.form('training_form'):
        test_size = st.slider('Tamaño de conjunto de prueba (%)', 10, 30, 20)
        submitted = st.form_submit_button('Ejecutar entrenamiento', type='primary')
        if submitted:
            st.info(f'Entrenando {model_type} con {test_size}% para validación...')
            with st.spinner('Procesando...'):
                st.success('Entrenamiento ejecutado correctamente en modo de demostración.')
