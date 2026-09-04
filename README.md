# Sistema de Mantenimiento Predictivo con IA - UNT

## Descripción
Aplicación web desarrollada con Python + Streamlit + PostgreSQL para la gestión de mantenimiento predictivo de equipos industriales en la gran minería, aplicando la metodología CRISP-DM y modelos avanzados de Inteligencia Artificial (Machine Learning y Deep Learning).

## Grupo
- **Cruz Esquivel Luis**
- **Paz Romero Alvaro Joseph**

## Curso
Ingeniería de Software II - IS-402  
Universidad Nacional de Trujillo  
Facultad de Ingeniería - Escuela de Ingeniería de Sistemas

## Requisitos
- Python 3.10+
- PostgreSQL 14+
- Git

## Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/Pandaman08/mantenimiento-predictivo-unt.git
cd mantenimiento-predictivo-unt
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
```

3. **Activar entorno virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

5. **Configurar variables de entorno:**
Copia el archivo de ejemplo `.env.example` a `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Edita `.env` con tus credenciales de PostgreSQL:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bd_mantenimientoproductivoUNT
DB_USER=postgres
DB_PASSWORD=postgres
JWT_SECRET_KEY=unt_secret_key_mantenimiento_predictivo_2026
JWT_EXPIRATION_HOURS=24
```

6. **Configurar base de datos PostgreSQL:**
```sql
CREATE DATABASE bd_mantenimientoproductivoUNT;
```
Ejecutar el script SQL de creación de esquema, restricciones y bitácora:
```bash
psql -U postgres -d bd_mantenimientoproductivoUNT -f db/schema.sql
```

7. **Generar datos sintéticos de telemetría y usuarios:**
```bash
python generate_data.py
```

## Ejecución
```bash
streamlit run app.py
```
La aplicación estará disponible en: `http://localhost:8501`

## Usuarios y Roles de Prueba

| Usuario | Contraseña | Rol | Descripción |
| --- | --- | --- | --- |
| `admin@unt.edu.pe` | `admin123` | Administrador | Control total del sistema, usuarios RBAC y configuración |
| `ingeniero@unt.edu.pe` | `admin123` | Ingeniero / Analista | Análisis EDA, modelado IA, validación y reportes |
| `supervisor@unt.edu.pe` | `admin123` | Supervisor | Monitor de flota, alertas, dashboards y reportes |
| `tecnico@unt.edu.pe` | `tec123` | Técnico / Operador | Diagnóstico en tiempo real y registro de lecturas |

## Estructura del Proyecto
```text
mantenimiento-predictivo-unt/
├── app.py                      # Aplicación principal Streamlit
├── generate_data.py            # Generador de datos sintéticos y poblamiento de DB
├── README.md                   # Documentación principal
├── RúbricaEvaluación.md        # Criterios de evaluación y rúbrica del curso
├── requirements.txt            # Dependencias del proyecto
├── config/                     # Configuración global y variables de entorno
│   └── settings.py
├── db/                         # Script DDL de PostgreSQL (≥8 tablas + bitácora)
│   └── schema.sql
├── data/                       # Dataset telemétrico de lecturas
│   └── synthetic_readings.csv
├── models/                     # Binarios y metadatos de modelos IA entrenados
├── src/                        # Capa de lógica de negocio y controladores
│   ├── auth/                   # Autenticación JWT + bcrypt + bitácora
│   │   └── auth_service.py
│   ├── db/                     # Conexión psycopg2 pool & operaciones SQL
│   │   ├── connection.py
│   │   └── db_operations.py
│   ├── evaluation/             # Evaluador, validación cruzada y significancia estadística
│   │   └── evaluator.py
│   ├── models/                 # Algoritmos tradicionales e híbridos
│   │   ├── deep_models.py
│   │   └── traditional_models.py
│   ├── preprocessing/          # Limpieza, normalización y ventanas temporales
│   │   └── preprocessor.py
│   └── reports/                # Generador de reportes PDF, Word y Excel
│       └── report_generator.py
├── tests/                      # Suite de pruebas unitarias e integración
└── ui/                         # Interfaz de usuario por componentes y fases CRISP-DM
    ├── components/
    └── pages/
```

## Características Implementadas
- ✅ Autenticación JWT + bcrypt con 4 roles y matriz de permisos RBAC
- ✅ Dashboard con KPIs (MTBF, MTTR, Disponibilidad) y gráficos interactivos
- ✅ Análisis Exploratorio de Datos (EDA) completo con distribuciones y correlaciones
- ✅ Motor de IA con 5 algoritmos (3 Tradicionales + 2 Híbridos Deep Learning)
- ✅ Aplicación rigurosa de las 6 fases de la metodología CRISP-DM
- ✅ Selección del mejor algoritmo mediante Matriz de Criterios Ponderados
- ✅ Validación cruzada con TimeSeriesSplit y Stratified K-Fold
- ✅ Optimización de hiperparámetros (RandomizedSearchCV y Keras Callbacks)
- ✅ Pruebas estadísticas (Test t pareado, Test de McNemar, Bootstrap CIs y Ruido)
- ✅ Base de datos PostgreSQL con 9 tablas, restricciones, FKs, índices y bitácora
- ✅ Exportación de reportes técnicos en PDF, Word (.docx) y Excel (.xlsx)

## Tecnologías Utilizadas
- **Lenguaje:** Python 3.10
- **Frontend / UI:** Streamlit & Vanilla CSS con Glassmorphism
- **Base de Datos:** PostgreSQL 14+ con psycopg2-binary
- **Machine Learning & Deep Learning:** scikit-learn, XGBoost, TensorFlow / Keras
- **Visualización:** Plotly, Seaborn, Matplotlib
- **Seguridad:** JWT (PyJWT), bcrypt
- **Reportes:** ReportLab (PDF), python-docx (Word), openpyxl (Excel)

---
*Universidad Nacional de Trujillo - 2026*
