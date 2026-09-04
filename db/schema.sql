-- Mining Predictive Maintenance Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ROLES TABLE
-- =====================================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PERMISOS TABLE
-- =====================================================
CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    recurso VARCHAR(100) NOT NULL,
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('leer', 'escribir', 'ejecutar')),
    concedido BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(rol_id, recurso, accion)
);

-- =====================================================
-- USUARIOS TABLE
-- =====================================================
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_login TIMESTAMP WITH TIME ZONE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    reset_token VARCHAR(255),
    reset_token_expira TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);

-- =====================================================
-- BITACORA_ACCESOS TABLE (AUDIT LOGS)
-- =====================================================
CREATE TABLE bitacora_accesos (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    ip_origen VARCHAR(45) DEFAULT '127.0.0.1',
    exitoso BOOLEAN NOT NULL DEFAULT TRUE,
    detalles TEXT,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bitacora_usuario_id ON bitacora_accesos(usuario_id);
CREATE INDEX idx_bitacora_email ON bitacora_accesos(email);
CREATE INDEX idx_bitacora_fecha ON bitacora_accesos(fecha_registro DESC);
CREATE INDEX idx_bitacora_accion ON bitacora_accesos(accion);

-- =====================================================
-- EQUIPOS TABLE
-- =====================================================
CREATE TABLE equipos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('pala', 'camion', 'perforadora')),
    fecha_instalacion DATE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'mantenimiento')),
    ubicacion VARCHAR(200),
    fabricante VARCHAR(100),
    modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_equipos_codigo ON equipos(codigo);
CREATE INDEX idx_equipos_tipo ON equipos(tipo);
CREATE INDEX idx_equipos_estado ON equipos(estado);

-- =====================================================
-- SENSORES TABLE
-- =====================================================
CREATE TABLE sensores (
    id SERIAL PRIMARY KEY,
    equipo_id INTEGER NOT NULL REFERENCES equipos(id) ON DELETE CASCADE,
    tipo_sensor VARCHAR(50) NOT NULL CHECK (tipo_sensor IN ('temperatura', 'presion_aceite', 'rpm', 'vibracion', 'horas_operacion')),
    unidad_medida VARCHAR(20) NOT NULL,
    rango_min NUMERIC(10, 2),
    rango_max NUMERIC(10, 2),
    ubicacion_sensor VARCHAR(100),
    fecha_instalacion DATE DEFAULT CURRENT_DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensores_equipo_id ON sensores(equipo_id);
CREATE INDEX idx_sensores_tipo_sensor ON sensores(tipo_sensor);
CREATE INDEX idx_sensores_activo ON sensores(activo);

-- =====================================================
-- LECTURAS TABLE
-- =====================================================
CREATE TABLE lecturas (
    id BIGSERIAL PRIMARY KEY,
    sensor_id INTEGER NOT NULL REFERENCES sensores(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    valor NUMERIC(12, 4) NOT NULL,
    calidad_dato SMALLINT NOT NULL DEFAULT 0 CHECK (calidad_dato IN (0, 1, 2)),
    -- 0 = ok, 1 = alerta, 2 = falla
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lecturas_sensor_id ON lecturas(sensor_id);
CREATE INDEX idx_lecturas_timestamp ON lecturas(timestamp DESC);
CREATE INDEX idx_lecturas_sensor_timestamp ON lecturas(sensor_id, timestamp DESC);
CREATE INDEX idx_lecturas_calidad ON lecturas(calidad_dato);

-- Partition by month for performance (optional, for large datasets)
-- CREATE TABLE lecturas_y2024m01 PARTITION OF lecturas
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- =====================================================
-- MODELOS_IA TABLE
-- =====================================================
CREATE TABLE modelos_ia (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('RandomForest', 'XGBoost', 'SVM', 'CNN-LSTM', 'LSTM-Autoencoder+RF')),
    hiperparametros JSONB NOT NULL DEFAULT '{}',
    metricas_evaluacion JSONB NOT NULL DEFAULT '{}',
    fecha_entrenamiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    entrenado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    descripcion TEXT
);

CREATE INDEX idx_modelos_tipo ON modelos_ia(tipo);
CREATE INDEX idx_modelos_activo ON modelos_ia(activo);
CREATE INDEX idx_modelos_fecha ON modelos_ia(fecha_entrenamiento DESC);

-- =====================================================
-- PREDICCIONES TABLE
-- =====================================================
CREATE TABLE predicciones (
    id BIGSERIAL PRIMARY KEY,
    equipo_id INTEGER NOT NULL REFERENCES equipos(id) ON DELETE CASCADE,
    modelo_id INTEGER NOT NULL REFERENCES modelos_ia(id) ON DELETE RESTRICT,
    timestamp_prediccion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    falla_predicha BOOLEAN NOT NULL,
    confianza NUMERIC(5, 4) NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
    timestamp_real_falla TIMESTAMP WITH TIME ZONE,
    usuario_ejecutor INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    datos_entrada JSONB,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predicciones_equipo_id ON predicciones(equipo_id);
CREATE INDEX idx_predicciones_modelo_id ON predicciones(modelo_id);
CREATE INDEX idx_predicciones_timestamp ON predicciones(timestamp_prediccion DESC);
CREATE INDEX idx_predicciones_falla ON predicciones(falla_predicha);
CREATE INDEX idx_predicciones_equipo_timestamp ON predicciones(equipo_id, timestamp_prediccion DESC);

-- =====================================================
-- REPORTES TABLE
-- =====================================================
CREATE TABLE reportes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(300) NOT NULL,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('PDF', 'Word', 'Excel')),
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generado_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    parametros_filtro JSONB NOT NULL DEFAULT '{}',
    equipo_id INTEGER REFERENCES equipos(id) ON DELETE SET NULL,
    fecha_inicio DATE,
    fecha_fin DATE
);

CREATE INDEX idx_reportes_generado_por ON reportes(generado_por);
CREATE INDEX idx_reportes_fecha ON reportes(fecha_generacion DESC);
CREATE INDEX idx_reportes_tipo ON reportes(tipo);

-- =====================================================
-- INITIAL DATA: ROLES
-- =====================================================
INSERT INTO roles (id, nombre, descripcion) VALUES
    (1, 'administrador', 'Control total del sistema: usuarios, configuraciones, modelos, equipos'),
    (2, 'supervisor', 'Acceso a dashboards, reportes, y gestión de equipos'),
    (3, 'operador', 'Visualización de datos y predicciones (solo lectura)'),
    (4, 'analista', 'Ejecutar entrenamientos, evaluar modelos y generar reportes avanzados')
ON CONFLICT (id) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    descripcion = EXCLUDED.descripcion;

-- =====================================================
-- INITIAL DATA: PERMISOS
-- =====================================================
-- Administrador: todos los permisos
INSERT INTO permisos (rol_id, recurso, accion, concedido) VALUES
    (1, 'dashboard', 'leer', true),
    (1, 'dashboard', 'escribir', true),
    (1, 'modelos', 'leer', true),
    (1, 'modelos', 'escribir', true),
    (1, 'modelos', 'ejecutar', true),
    (1, 'reportes', 'leer', true),
    (1, 'reportes', 'escribir', true),
    (1, 'reportes', 'ejecutar', true),
    (1, 'usuarios', 'leer', true),
    (1, 'usuarios', 'escribir', true),
    (1, 'usuarios', 'ejecutar', true),
    (1, 'equipos', 'leer', true),
    (1, 'equipos', 'escribir', true),
    (1, 'equipos', 'ejecutar', true),
    (1, 'entrenamiento', 'leer', true),
    (1, 'entrenamiento', 'escribir', true),
    (1, 'entrenamiento', 'ejecutar', true),
    (1, 'prediccion', 'leer', true),
    (1, 'prediccion', 'escribir', true),
    (1, 'prediccion', 'ejecutar', true),
    (1, 'admin', 'leer', true),
    (1, 'admin', 'escribir', true),
    (1, 'admin', 'ejecutar', true),
    (1, 'evaluacion', 'leer', true),
    (1, 'evaluacion', 'ejecutar', true)
ON CONFLICT (rol_id, recurso, accion) DO UPDATE SET concedido = EXCLUDED.concedido;

-- Supervisor
INSERT INTO permisos (rol_id, recurso, accion, concedido) VALUES
    (2, 'dashboard', 'leer', true),
    (2, 'modelos', 'leer', true),
    (2, 'reportes', 'leer', true),
    (2, 'reportes', 'ejecutar', true),
    (2, 'equipos', 'leer', true),
    (2, 'equipos', 'escribir', true),
    (2, 'prediccion', 'leer', true),
    (2, 'prediccion', 'ejecutar', true)
ON CONFLICT (rol_id, recurso, accion) DO UPDATE SET concedido = EXCLUDED.concedido;

-- Operador
INSERT INTO permisos (rol_id, recurso, accion, concedido) VALUES
    (3, 'dashboard', 'leer', true),
    (3, 'prediccion', 'leer', true),
    (3, 'prediccion', 'ejecutar', true)
ON CONFLICT (rol_id, recurso, accion) DO UPDATE SET concedido = EXCLUDED.concedido;

-- Analista
INSERT INTO permisos (rol_id, recurso, accion, concedido) VALUES
    (4, 'dashboard', 'leer', true),
    (4, 'modelos', 'leer', true),
    (4, 'modelos', 'ejecutar', true),
    (4, 'reportes', 'leer', true),
    (4, 'reportes', 'ejecutar', true),
    (4, 'entrenamiento', 'leer', true),
    (4, 'entrenamiento', 'escribir', true),
    (4, 'entrenamiento', 'ejecutar', true),
    (4, 'evaluacion', 'leer', true),
    (4, 'evaluacion', 'ejecutar', true),
    (4, 'prediccion', 'leer', true),
    (4, 'prediccion', 'ejecutar', true)
ON CONFLICT (rol_id, recurso, accion) DO UPDATE SET concedido = EXCLUDED.concedido;

-- =====================================================
-- DEFAULT ADMIN USER (password: admin123 - hashed with bcrypt)
-- =====================================================
-- Insert will be done via Python script to properly hash password

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View: Latest sensor readings per equipment
CREATE OR REPLACE VIEW v_ultimas_lecturas AS
SELECT DISTINCT ON (e.id, s.tipo_sensor)
    e.id AS equipo_id,
    e.codigo AS equipo_codigo,
    e.nombre AS equipo_nombre,
    e.tipo AS equipo_tipo,
    s.id AS sensor_id,
    s.tipo_sensor,
    s.unidad_medida,
    l.timestamp,
    l.valor,
    l.calidad_dato
FROM equipos e
JOIN sensores s ON s.equipo_id = e.id AND s.activo = true
JOIN lecturas l ON l.sensor_id = s.id
WHERE e.estado = 'activo'
ORDER BY e.id, s.tipo_sensor, l.timestamp DESC;

-- View: Equipment health summary
CREATE OR REPLACE VIEW v_resumen_salud_equipos AS
SELECT
    e.id,
    e.codigo,
    e.nombre,
    e.tipo,
    e.estado,
    COUNT(DISTINCT s.id) AS total_sensores,
    COUNT(l.id) AS total_lecturas_ultimas_24h,
    MAX(l.timestamp) AS ultima_lectura,
    AVG(CASE WHEN s.tipo_sensor = 'temperatura' THEN l.valor END) AS temp_promedio,
    AVG(CASE WHEN s.tipo_sensor = 'vibracion' THEN l.valor END) AS vib_promedio,
    COUNT(CASE WHEN l.calidad_dato > 0 THEN 1 END) AS alertas_activas
FROM equipos e
LEFT JOIN sensores s ON s.equipo_id = e.id AND s.activo = true
LEFT JOIN lecturas l ON l.sensor_id = s.id AND l.timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY e.id, e.codigo, e.nombre, e.tipo, e.estado;

-- View: Prediction accuracy tracking
CREATE OR REPLACE VIEW v_precision_modelos AS
SELECT
    m.id AS modelo_id,
    m.nombre AS modelo_nombre,
    m.tipo AS modelo_tipo,
    COUNT(p.id) AS total_predicciones,
    COUNT(CASE WHEN p.falla_predicha = true AND p.timestamp_real_falla IS NOT NULL THEN 1 END) AS verdaderos_positivos,
    COUNT(CASE WHEN p.falla_predicha = false AND p.timestamp_real_falla IS NOT NULL THEN 1 END) AS falsos_negativos,
    COUNT(CASE WHEN p.falla_predicha = true AND p.timestamp_real_falla IS NULL THEN 1 END) AS falsos_positivos,
    COUNT(CASE WHEN p.falla_predicha = false AND p.timestamp_real_falla IS NULL THEN 1 END) AS verdaderos_negativos,
    ROUND(
        COUNT(CASE WHEN p.falla_predicha = true AND p.timestamp_real_falla IS NOT NULL THEN 1 END)::numeric /
        NULLIF(COUNT(CASE WHEN p.falla_predicha = true THEN 1 END), 0) * 100, 2
    ) AS precision_porcentual,
    ROUND(
        COUNT(CASE WHEN p.falla_predicha = true AND p.timestamp_real_falla IS NOT NULL THEN 1 END)::numeric /
        NULLIF(COUNT(CASE WHEN p.timestamp_real_falla IS NOT NULL THEN 1 END), 0) * 100, 2
    ) AS recall_porcentual
FROM modelos_ia m
LEFT JOIN predicciones p ON p.modelo_id = m.id
WHERE m.activo = true
GROUP BY m.id, m.nombre, m.tipo;

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for equipos
CREATE TRIGGER update_equipos_updated_at
    BEFORE UPDATE ON equipos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean old predictions (keep last 1 year)
CREATE OR REPLACE FUNCTION limpiar_predicciones_antiguas()
RETURNS INTEGER AS $$
DECLARE
    rows_deleted INTEGER;
BEGIN
    DELETE FROM predicciones
    WHERE timestamp_prediccion < NOW() - INTERVAL '1 year'
    AND timestamp_real_falla IS NULL;
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RETURN rows_deleted;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- GRANTS (adjust as needed for production)
-- =====================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mining_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mining_app;