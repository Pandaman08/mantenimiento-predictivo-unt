# Sistema de Mantenimiento Predictivo - UNT

Aplicación de analítica predictiva para mantenimiento de equipos con Streamlit, PostgreSQL y modelos de IA.

# Ingeniería de Software II - IS-402 Universidad Nacional de Trujillo

# Integrantes
  - Cruz Esquivel Luis
  - Paz Romero Alvaro Joseph

## Requisitos previos

- Python 3.10 o 3.11
- PostgreSQL 14+
- Git
## Clonar repositorio
```bash
git clone https://github.com/Pandaman08/mantenimiento-predictivo-unt.git
cd mantenimiento-predictivo-unt

```bash
python -m venv venv
```

## 2) Activar entorno virtual

En Linux/macOS:

```bash
source venv/bin/activate
```

En Windows:

```bash
venv\Scripts\activate
```

## 3) Instalar dependencias

```bash
pip install -r requirements.txt
```

## 4) Configurar variables de entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mining_maintenance
DB_USER=postgres
DB_PASS=postgres
JWT_SECRET=your-super-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24
```

## 5) Crear la base de datos PostgreSQL

```sql
CREATE DATABASE mining_maintenance;
```

Luego ejecuta el script SQL:

```bash
psql -h localhost -U postgres -d mining_maintenance -f db/schema.sql
```

## 6) Generar datos sintéticos

```bash
python generate_data.py
```

Este paso crea equipos, sensores y lecturas de ejemplo para alimentar la UI y los modelos.

## 7) Ejecutar la aplicación

```bash
streamlit run app.py
```

Abra la URL mostrada por Streamlit en el navegador.

## 8) Credenciales por defecto

La base de datos incluye un usuario administrador por defecto con:

- Email: `admin@unt.edu.pe`
- Contraseña: `admin123`

## 9) Flujo recomendado

1. Inicie sesión.
2. Revise la fase de negocio y EDA.
3. Prepare y entrene modelos.
4. Evalúe resultados.
5. Genere reportes PDF, Word o Excel.
6. Use la predicción en tiempo real.
