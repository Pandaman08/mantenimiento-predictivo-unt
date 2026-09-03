import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from config.settings import settings
from src.db.connection import db_pool


class DBOperations:
    @staticmethod
    def _to_json(value: Any) -> str:
        return json.dumps(value, default=str, ensure_ascii=False)

    @staticmethod
    def save_model_record(
        nombre: str,
        model_type: str,
        model_obj: Any,
        hiperparametros: Dict[str, Any],
        metricas_evaluacion: Dict[str, Any],
        entrenado_por: Optional[int] = None,
        description: str = "",
        extension: str = "joblib",
    ) -> int:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in nombre.lower())
        file_name = f"{safe_name}_{timestamp}.{extension}"
        storage_path = settings.MODELS_DIR / file_name

        if hasattr(model_obj, 'save') and not isinstance(model_obj, (str, bytes)):
            model_obj.save(str(storage_path))
        else:
            joblib.dump(model_obj, str(storage_path))

        with db_pool.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO modelos_ia (
                    nombre, tipo, hiperparametros, metricas_evaluacion,
                    fecha_entrenamiento, entrenado_por, ruta_archivo,
                    version, activo, descripcion
                ) VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    nombre,
                    model_type,
                    DBOperations._to_json(hiperparametros),
                    DBOperations._to_json(metricas_evaluacion),
                    datetime.utcnow(),
                    entrenado_por,
                    str(storage_path),
                    '1.0.0',
                    True,
                    description,
                ),
            )
            row = cursor.fetchone()
            return int(row['id'])

    @staticmethod
    def save_prediction(
        equipo_id: int,
        modelo_id: int,
        falla_predicha: bool,
        confianza: float,
        usuario_ejecutor: Optional[int],
        datos_entrada: Optional[Dict[str, Any]] = None,
        timestamp_real_falla: Optional[datetime] = None,
    ) -> int:
        with db_pool.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO predicciones (
                    equipo_id, modelo_id, timestamp_prediccion,
                    falla_predicha, confianza, timestamp_real_falla,
                    usuario_ejecutor, datos_entrada
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    equipo_id,
                    modelo_id,
                    datetime.utcnow(),
                    falla_predicha,
                    float(confianza),
                    timestamp_real_falla,
                    usuario_ejecutor,
                    DBOperations._to_json(datos_entrada or {}),
                ),
            )
            row = cursor.fetchone()
            return int(row['id'])

    @staticmethod
    def save_report(
        nombre: str,
        report_type: str,
        ruta_archivo: str,
        parametros_filtro: Dict[str, Any],
        generado_por: Optional[int] = None,
        equipo_id: Optional[int] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
    ) -> int:
        with db_pool.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO reportes (
                    nombre, tipo, fecha_generacion, generado_por,
                    ruta_archivo, parametros_filtro, equipo_id,
                    fecha_inicio, fecha_fin
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                RETURNING id
                """,
                (
                    nombre,
                    report_type.upper(),
                    datetime.utcnow(),
                    generado_por,
                    ruta_archivo,
                    DBOperations._to_json(parametros_filtro),
                    equipo_id,
                    fecha_inicio,
                    fecha_fin,
                ),
            )
            row = cursor.fetchone()
            return int(row['id'])


db_operations = DBOperations()
