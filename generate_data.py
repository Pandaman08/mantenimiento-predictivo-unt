import os
import random
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from config.settings import settings
from src.auth.auth_service import AuthService
from src.db.connection import db_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    def __init__(self, n_equipos: int = 5, n_records: int = 10000, days_back: int = 730):
        self.n_equipos = n_equipos
        self.n_records = n_records
        self.days_back = days_back
        self.equipos = []
        self.sensores = {}

        # Equipment specifications for realistic ranges
        self.equip_specs = {
            'pala': {
                'temperatura': {'mean': 85, 'std': 10, 'min': 50, 'max': 130},
                'presion_aceite': {'mean': 180, 'std': 20, 'min': 100, 'max': 280},
                'rpm': {'mean': 1800, 'std': 200, 'min': 1200, 'max': 2400},
                'vibracion': {'mean': 2.5, 'std': 0.8, 'min': 0.5, 'max': 8.0},
                'horas_operacion': {'mean': 2000, 'std': 250, 'min': 0, 'max': 20000, 'increment': 1}
            },
            'camion': {
                'temperatura': {'mean': 95, 'std': 12, 'min': 60, 'max': 140},
                'presion_aceite': {'mean': 160, 'std': 15, 'min': 80, 'max': 250},
                'rpm': {'mean': 2000, 'std': 250, 'min': 1400, 'max': 2600},
                'vibracion': {'mean': 3.0, 'std': 1.0, 'min': 0.8, 'max': 10.0},
                'horas_operacion': {'mean': 2200, 'std': 260, 'min': 0, 'max': 22000, 'increment': 1}
            },
            'perforadora': {
                'temperatura': {'mean': 75, 'std': 8, 'min': 40, 'max': 120},
                'presion_aceite': {'mean': 200, 'std': 25, 'min': 120, 'max': 300},
                'rpm': {'mean': 1500, 'std': 180, 'min': 1000, 'max': 2000},
                'vibracion': {'mean': 4.0, 'std': 1.5, 'min': 1.0, 'max': 12.0},
                'horas_operacion': {'mean': 1800, 'std': 220, 'min': 0, 'max': 18000, 'increment': 1}
            }
        }

    def create_equipos_and_sensores(self):
        """Create equipment and sensors in database"""
        tipos = ['pala', 'camion', 'perforadora']
        nombres_tipo = {
            'pala': ['Pala Hidráulica PH-', 'Pala Eléctrica PE-', 'Pala de Cable PC-'],
            'camion': ['Camión Minero CM-', 'Camión de Acarreo CA-', 'Camión Articulado CART-'],
            'perforadora': ['Perforadora Rotativa PR-', 'Perforadora de Fondo PF-', 'Perforadora Diamantina PD-']
        }

        with db_pool.get_cursor() as cursor:
            for i in range(self.n_equipos):
                tipo = random.choice(tipos)
                nombre_base = random.choice(nombres_tipo[tipo])
                codigo = f"{tipo.upper()[:3]}-{i+1:03d}"
                nombre = f"{nombre_base}{i+1:03d}"
                fecha_instalacion = datetime.now().date() - timedelta(days=random.randint(30, 1000))

                cursor.execute("""
                    INSERT INTO equipos (codigo, nombre, tipo, fecha_instalacion, estado, ubicacion, fabricante, modelo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (codigo, nombre, tipo, fecha_instalacion, 'activo',
                      f"Zona {random.randint(1,5)}",
                      random.choice(['Caterpillar', 'Komatsu', 'Hitachi', 'Liebherr', 'Sandvik']),
                      f"Modelo {random.randint(100, 999)}"))

                equipo_id = cursor.fetchone()['id']
                self.equipos.append({'id': equipo_id, 'codigo': codigo, 'tipo': tipo, 'nombre': nombre})

                # Create sensors for each equipment
                sensor_configs = [
                    ('temperatura', '°C'),
                    ('presion_aceite', 'PSI'),
                    ('rpm', 'RPM'),
                    ('vibracion', 'mm/s'),
                    ('horas_operacion', 'horas')
                ]

                for sensor_tipo, unidad in sensor_configs:
                    specs = self.equip_specs[tipo][sensor_tipo]
                    cursor.execute("""
                        INSERT INTO sensores (equipo_id, tipo_sensor, unidad_medida, rango_min, rango_max, activo)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (equipo_id, sensor_tipo, unidad, specs['min'], specs['max'], True))

                    sensor_id = cursor.fetchone()['id']
                    if equipo_id not in self.sensores:
                        self.sensores[equipo_id] = {}
                    self.sensores[equipo_id][sensor_tipo] = sensor_id

    def generate_failure_events(self, equipo_id: int, start_date: datetime, end_date: datetime) -> list:
        """Generate failure events for an equipment"""
        failures = []
        n_failures = random.randint(3, 8)  # 3-8 failures in 2 years

        for _ in range(n_failures):
            failure_time = start_date + timedelta(
                days=random.uniform(0, (end_date - start_date).days)
            )
            # Failure lasts 2-8 hours
            duration = timedelta(hours=random.uniform(2, 8))
            failures.append({
                'start': failure_time,
                'end': failure_time + duration,
                'degradation_start': failure_time - timedelta(hours=random.uniform(24, 72))
            })
        return failures

    def generate_sensor_readings(self, equipo: dict, failures: list) -> list:
        """Generate realistic sensor readings with degradation patterns"""
        readings = []
        tipo = equipo['tipo']
        specs = self.equip_specs[tipo]
        sensores = self.sensores[equipo['id']]

        start_date = datetime.now() - timedelta(days=self.days_back)
        end_date = datetime.now()
        total_hours = int((end_date - start_date).total_seconds() / 3600)

        # Sample readings (not every hour to get ~10000 total)
        sample_interval = max(1, total_hours // (self.n_records // self.n_equipos))

        horas_acumuladas = 0
        current_temp = specs['temperatura']['mean']
        current_presion = specs['presion_aceite']['mean']
        current_rpm = specs['rpm']['mean']
        current_vib = specs['vibracion']['mean']

        for hour in range(0, total_hours, sample_interval):
            timestamp = start_date + timedelta(hours=hour)
            horas_acumuladas += sample_interval

            # Check if in degradation period or failure
            in_degradation = False
            in_failure = False
            degradation_factor = 0

            for failure in failures:
                if failure['start'] <= timestamp <= failure['end']:
                    in_failure = True
                    degradation_factor = 1.0
                    break
                elif failure['degradation_start'] <= timestamp < failure['start']:
                    in_degradation = True
                    # Gradual degradation
                    hours_before_failure = (failure['start'] - timestamp).total_seconds() / 3600
                    degradation_factor = max(0, 1 - hours_before_failure / 48)
                    break

            # Base values with daily/weekly cycles
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()

            # Daily cycle (cooler at night)
            daily_cycle = np.sin(2 * np.pi * hour_of_day / 24) * 5
            # Weekly cycle (less usage on weekends)
            weekly_cycle = -2 if day_of_week >= 5 else 0

            # Generate readings for each sensor
            for sensor_tipo, sensor_id in sensores.items():
                spec = specs[sensor_tipo]
                base_value = spec['mean']

                if sensor_tipo == 'temperatura':
                    value = base_value + daily_cycle + weekly_cycle + np.random.normal(0, spec['std'])
                    if in_degradation:
                        value += degradation_factor * 15 * np.random.uniform(0.5, 1.5)
                    elif in_failure:
                        value += 25 * np.random.uniform(0.8, 1.2)

                elif sensor_tipo == 'presion_aceite':
                    value = base_value + weekly_cycle + np.random.normal(0, spec['std'])
                    if in_degradation:
                        value -= degradation_factor * 20 * np.random.uniform(0.5, 1.5)
                    elif in_failure:
                        value -= 40 * np.random.uniform(0.7, 1.3)

                elif sensor_tipo == 'rpm':
                    value = base_value + np.random.normal(0, spec['std'])
                    if in_degradation:
                        value += degradation_factor * 100 * np.random.uniform(-0.5, 0.5)
                    elif in_failure:
                        value += 200 * np.random.uniform(-1, 1)

                elif sensor_tipo == 'vibracion':
                    value = max(0.1, base_value + np.random.normal(0, spec['std']))
                    if in_degradation:
                        value *= (1 + degradation_factor * 2 * np.random.uniform(0.5, 1.5))
                    elif in_failure:
                        value *= 3 * np.random.uniform(1.5, 2.5)

                elif sensor_tipo == 'horas_operacion':
                    value = horas_acumuladas

                # Clip to realistic ranges
                value = np.clip(value, spec['min'], spec['max'])

                # Determine quality
                calidad = 0
                if in_failure:
                    calidad = 2
                elif in_degradation or value > spec['max'] * 0.9 or value < spec['min'] * 1.1:
                    calidad = 1

                # Add missing data (5%)
                if random.random() < 0.05:
                    continue

                readings.append({
                    'sensor_id': sensor_id,
                    'timestamp': timestamp,
                    'valor': round(value, 2),
                    'calidad_dato': calidad
                })

        return readings

    def generate_target_variable(self, readings_df: pd.DataFrame, failures: list) -> pd.DataFrame:
        """Generate target variable: failure in next 24 hours"""
        readings_df = readings_df.copy()
        readings_df['falla'] = 0

        for failure in failures:
            # Mark 24 hours before failure as positive
            window_start = failure['degradation_start']
            window_end = failure['start']
            mask = (readings_df['timestamp'] >= window_start) & (readings_df['timestamp'] <= window_end)
            readings_df.loc[mask, 'falla'] = 1

        return readings_df

    def run(self):
        """Main generation pipeline"""
        logger.info("Starting synthetic data generation...")

        # Initialize database connection
        db_pool.initialize()

        # Create equipment and sensors
        logger.info("Creating equipment and sensors...")
        self.create_equipos_and_sensores()

        # Generate readings for each equipment
        all_readings = []
        for equipo in self.equipos:
            logger.info(f"Generating data for {equipo['codigo']} ({equipo['tipo']})...")
            failures = self.generate_failure_events(
                equipo['id'],
                datetime.now() - timedelta(days=self.days_back),
                datetime.now()
            )
            readings = self.generate_sensor_readings(equipo, failures)

            # Convert to DataFrame and add target
            df = pd.DataFrame(readings)
            if not df.empty:
                df = self.generate_target_variable(df, failures)
                all_readings.append(df)

        # Combine all readings
        final_df = pd.concat(all_readings, ignore_index=True)
        final_df = final_df.sort_values('timestamp').reset_index(drop=True)

        logger.info(f"Generated {len(final_df)} readings")
        logger.info(f"Failure rate: {final_df['falla'].mean():.2%}")

        # Save to CSV for backup
        csv_path = settings.DATA_DIR / "synthetic_readings.csv"
        final_df.to_csv(csv_path, index=False)
        logger.info(f"Data saved to {csv_path}")

        # Insert into database
        logger.info("Inserting readings into database...")
        self.insert_readings(final_df)
        self.ensure_default_admin()

        logger.info("Data generation completed!")
        return final_df

    def ensure_default_admin(self):
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute("SELECT id FROM usuarios WHERE email = %s", ('admin@unt.edu.pe',))
                if cursor.fetchone():
                    logger.info('Default admin already exists.')
                    return

                role = 1
                user_service = AuthService()
                password_hash = user_service.hash_password('admin123')
                cursor.execute(
                    """
                    INSERT INTO usuarios (nombre, email, contrasena_hash, rol_id, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    ('Administrador', 'admin@unt.edu.pe', password_hash, role, True),
                )
                logger.info('Default admin created: admin@unt.edu.pe / admin123')
        except Exception as exc:
            logger.warning(f'Could not create default admin user: {exc}')

    def insert_readings(self, df: pd.DataFrame, batch_size: int = 1000):
        """Insert readings into database in batches"""
        query = """
            INSERT INTO lecturas (sensor_id, timestamp, valor, calidad_dato)
            VALUES (%s, %s, %s, %s)
        """

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            data = [(row['sensor_id'], row['timestamp'], row['valor'], row['calidad_dato'])
                    for _, row in batch.iterrows()]

            with db_pool.get_cursor() as cursor:
                cursor.executemany(query, data)

            if i % 5000 == 0:
                logger.info(f"Inserted {i}/{len(df)} readings")

def main():
    db_pool.initialize()
    generator = SyntheticDataGenerator(n_equipos=5, n_records=10000, days_back=730)
    generator.run()

if __name__ == "__main__":
    main()