## 9. CRITERIOS DE EVALUACIÓN (RÚBRICA)

| N° | Criterio de Evaluación | Puntaje | Nivel de Logro |
| --- | --- | --- | --- |
|  |  |  | Excelente (100%) / Bueno (70%) / Regular (40%) / Insuficiente (0%) |
| 1 | FUNCIONALIDAD DE MÓDULOS OBLIGATORIOS | 30 pts |  |
|  | 1.1 Autenticación y usuarios con 4 roles | 5 |  |
|  | 1.2 Dashboard con KPIs y gráficos interactivos | 5 |  |
|  | 1.3 EDA completo con visualizaciones | 5 |  |
|  | 1.4 Motor de IA con 5 algoritmos | 10 |  |
|  | 1.5 Reportes en PDF, Word y Excel | 5 |  |
| 2 | MOTOR DE IA Y METODOLOGÍA CRISP-DM | 25 pts |  |
|  | 2.1 Aplicación de las 6 fases CRISP-DM | 10 |  |
|  | 2.2 Implementación de 3 algoritmos tradicionales | 5 |  |
|  | 2.3 Implementación de 2 algoritmos híbridos | 5 |  |
|  | 2.4 Selección de mejor algoritmo con criterios ponderados | 5 |  |
| 3 | ANÁLISIS ESTADÍSTICO ROBUSTO | 15 pts |  |
|  | 3.1 Validación cruzada con múltiples estrategias | 5 |  |
|  | 3.2 Optimización de hiperparámetros | 5 |  |
|  | 3.3 Pruebas estadísticas robustas | 5 |  |
| 4 | BASE DE DATOS POSTGRESQL | 10 pts |  |
|  | 4.1 Diseño del modelo ER (≥8 tablas) | 5 |  |
|  | 4.2 Implementación de restricciones y relaciones | 3 |  |
|  | 4.3 Datos de prueba insertados | 2 |  |
| 5 | GESTIÓN DE USUARIOS Y SEGURIDAD | 10 pts |  |
|  | 5.1 Sistema de autenticación JWT + bcrypt | 4 |  |
|  | 5.2 4 roles con matriz de permisos | 4 |  |
|  | 5.3 Bitácora de accesos | 2 |  |
| 6 | CALIDAD DE CÓDIGO Y DOCUMENTACIÓN | 10 pts |  |
|  | 6.1 Modularidad y reutilización | 3 |  |
|  | 6.2 Comentarios y nombres descriptivos | 3 |  |
|  | 6.3 README.md completo | 2 |  |
|  | 6.4 Presentación oral | 2 |  |
|  | TOTAL | 100 pts |  |

### 📝 Escala de Calificación

| Rango | Calificación |
| --- | --- |
| 90 - 100 | Excelente (AD) |
| 80 - 89 | Muy Bueno (MB) |
| 70 - 79 | Bueno (B) |
| 60 - 69 | Suficiente (S) |
| 0 - 59 | Insuficiente (I) |

## 10. ENTREGABLES
Cada grupo deberá entregar los siguientes archivos en un archivo **ZIP** a través del aula virtual:

| N° | Entregable | Formato | Peso del puntaje |
| --- | --- | --- | --- |
| 1 | Código fuente completo del proyecto | Carpeta comprimida | 60% |
| 2 | Script de base de datos PostgreSQL | .sql | 10% |
| 3 | Archivo requirements.txt | .txt | 5% |
| 4 | Archivo README.md con instrucciones | .md | 10% |
| 5 | Documento de la práctica | .pdf | 10% |
| 6 | Presentación diapositivas | .pptx / .pdf | 5% |
| 7 | Video demostrativo (opcional, 5 min) | .mp4 | Puntos adicionales |

**Fecha límite de entrega:** Final de la Sesión 4
**Formato de nombre de archivo:** IS402_GrupoXX_Practica05.zip

## 11. RECOMENDACIONES
**Trabajo colaborativo:** Utilizar Git y GitHub para el control de versiones. Crear un repositorio privado por grupo.
**Commits**** frecuentes:** Realizar commits descriptivos por cada funcionalidad implementada. Ejemplo: feat: agregar módulo de autenticación JWT
**Pruebas continuas:** Probar cada módulo de manera independiente antes de integrarlo al sistema completo.
**Documentación temprana:** Comentar el código mientras se desarrolla, no dejarlo para el final.
**Consulta oportuna:** Resolver dudas con el docente durante las sesiones de laboratorio o por correo electrónico.
**Gestión del tiempo:** Distribuir las actividades equitativamente entre las 4 sesiones. No dejar todo para la última sesión.
**Recursos adicionales:** Consultar la documentación oficial de Streamlit, scikit-learn, TensorFlow y PostgreSQL.
**Estándares de código:** Seguir las convenciones PEP 8 para Python. Usar nombres descriptivos para variables y funciones.

## 12. REFERENCIAS BIBLIOGRÁFICAS
Wirth, R., & Hipp, J. (2000). **CRISP-DM: Towards a standard process model for data mining**. Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining.
Géron, A. (2022). **Hands-On Machine Learning with Scikit-Learn, ****Keras****, and TensorFlow** (3ra edición). O’Reilly Media.
Sumathi, S., & Sivanandam, S. N. (2018). **Introduction to Data Mining and its Applications**. Springer.
Chacon, S., & Straub, B. (2014). **Pro Git** (2da edición). Apress.
**Documentación oficial de ****Streamlit****:** https://docs.streamlit.io/
**Documentación oficial de PostgreSQL:** https://www.postgresql.org/docs/
**Documentación de ****scikit-learn****:** https://scikit-learn.org/stable/documentation.html
**Documentación de ****XGBoost****:** https://xgboost.readthedocs.io/
**Universidad Nacional de Trujillo - Vicerrectorado Académico:** Normas para trabajos de investigación y prácticas de laboratorio.
**Ministerio de Energía y Minas del Perú:** Estadísticas de la industria minera peruana.

## 13. ANEXOS
### Anexo A: Comandos Útiles de PostgreSQL
-- Crear base de datos
CREATE DATABASE mantenimiento_predictivo;

-- Crear usuario
CREATE USER usuario_practica WITH PASSWORD '123456';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE mantenimiento_predictivo TO usuario_practica;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO usuario_practica;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO usuario_practica;

-- Respaldar base de datos
pg_dump -U postgres mantenimiento_predictivo > respaldo.sql

-- Restaurar base de datos
psql -U postgres mantenimiento_predictivo < respaldo.sql
### Anexo B: Troubleshooting Común

| Problema | Solución |
| --- | --- |
| Error de conexión PostgreSQL | Verificar que el servicio esté iniciado (services.msc en Windows, systemctl start postgresql en Linux). Comprobar credenciales y puerto. |
| Streamlit no abre el navegador | Copiar y pegar manualmente la URL mostrada en la consola (generalmente http://localhost:8501) |
| Error al instalar librerías | Actualizar pip primero: pip install --upgrade pip. Usar --user si hay problemas de permisos. |
| TensorFlow no instala | Verificar compatibilidad con la versión de Python. Usar Python 3.10. En Windows, puede requerir Microsoft Visual C++ Redistributable. |
| ImportError en módulos | Verificar que exista el archivo __init__.py en cada carpeta de módulos. Verificar la ruta de importación. |
| Error de bcrypt en Windows | Instalar Microsoft Visual C++ Build Tools o usar bcrypt desde conda. |
| JWT inválido | Verificar que la clave secreta sea la misma para generar y validar tokens. Verificar que el token no haya expirado. |

### Anexo C: Matriz de Roles y Permisos Sugerida

| Módulo | Administrador | Ingeniero | Supervisor | Técnico |
| --- | --- | --- | --- | --- |
| Dashboard | ✅ Lectura/Escritura | ✅ Lectura/Escritura | ✅ Lectura | ✅ Lectura |
| EDA | ✅ Completo | ✅ Completo | ✅ Solo lectura | ⚠️ Limitado |
| Motor IA | ✅ Completo | ✅ Completo | ⚠️ Solo consulta | ❌ Sin acceso |
| Validación Cruzada | ✅ Completo | ✅ Completo | ❌ Sin acceso | ❌ Sin acceso |
| Optimización | ✅ Completo | ✅ Completo | ❌ Sin acceso | ❌ Sin acceso |
| Pruebas Estadísticas | ✅ Completo | ✅ Completo | ❌ Sin acceso | ❌ Sin acceso |
| Gestión Usuarios | ✅ Completo | ❌ Sin acceso | ❌ Sin acceso | ❌ Sin acceso |
| Reportes | ✅ Generar/Ver | ✅ Generar/Ver | ✅ Ver | ⚠️ Ver limitado |
| Mantenimiento | ✅ Completo | ✅ Completo | ✅ Crear/Ver | ✅ Ejecutar |
| Repuestos | ✅ Completo | ✅ Completo | ✅ Ver/Actualizar | ✅ Ver |
| Bitácora | ✅ Completo | ❌ Sin acceso | ❌ Sin acceso | ❌ Sin acceso |

### Anexo D: Ejemplo de Archivo README.md
# Sistema de Mantenimiento Predictivo con IA

## Descripción
Aplicación web desarrollada con Python + Streamlit + PostgreSQL para la gestión de mantenimiento predictivo de equipos industriales usando inteligencia artificial.

## Grupo
- Integrante 1
- Integrante 2
- Integrante 3

## Curso
Ingeniería de Software II - IS-402  
Universidad Nacional de Trujillo

## Requisitos
- Python 3.10+
- PostgreSQL 14+

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/usuario/proyecto.git
cd proyecto
Crear entorno virtual:
python -m venv venv
Activar entorno virtual:
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
Instalar dependencias:
pip install -r requirements.txt
Configurar base de datos:
# Crear base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE mantenimiento_predictivo;"

# Ejecutar script de creación
psql -U postgres -d mantenimiento_predictivo -f database/schema.sql

# Insertar datos de prueba
psql -U postgres -d mantenimiento_predictivo -f database/datos_prueba.sql
Configurar variables de entorno (opcional):
# Windows
set DB_HOST=localhost
set DB_NAME=mantenimiento_predictivo
set DB_USER=postgres
set DB_PASSWORD=tu_contraseña

# Linux/Mac
export DB_HOST=localhost
export DB_NAME=mantenimiento_predictivo
export DB_USER=postgres
export DB_PASSWORD=tu_contraseña
## Ejecución
streamlit run app.py
La aplicación estará disponible en: http://localhost:8501
## Usuarios de Prueba

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| admin | admin123 | Administrador |
| ingeniero | inge123 | Ingeniero |
| supervisor | super123 | Supervisor |
| tecnico | tec123 | Técnico |

## Estructura del Proyecto
[Incluir árbol de directorios]
## Características Implementadas
✅ Autenticación con roles y permisos
✅ Dashboard con KPIs y gráficos
✅ Análisis Exploratorio de Datos (EDA)
✅ Motor de IA con 5 algoritmos
✅ Validación cruzada robusta
✅ Optimización de hiperparámetros
✅ Pruebas estadísticas
✅ Reportes en PDF, Word y Excel
## Tecnologías
Python 3.10
Streamlit
PostgreSQL
scikit-learn, XGBoost, TensorFlow
Plotly, ReportLab, python-docx, openpyxl
JWT, bcrypt ```

**Trujillo, ****septiembre**** de 2026**

*“La ingeniería de software no es solo escribir código, es crear soluciones que generen valor real para la sociedad”*

**Fin de la Guía de Práctica de Laboratorio ****N°**** 05**
