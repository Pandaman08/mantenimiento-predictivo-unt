import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    def __init__(self):
        self.DB_HOST = os.getenv("DB_HOST", "localhost")
        self.DB_PORT = int(os.getenv("DB_PORT", "5432"))
        self.DB_NAME = os.getenv("DB_NAME", "mining_maintenance")
        self.DB_USER = os.getenv("DB_USER", "postgres")
        self.DB_PASS = os.getenv("DB_PASS", os.getenv("DB_PASSWORD", "postgres"))
        self.DB_PASSWORD = self.DB_PASS
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production"))
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        self.BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
        self.MODELS_DIR = BASE_DIR / "models"
        self.MODELS_DIR.mkdir(exist_ok=True)
        self.REPORTS_DIR = BASE_DIR / "reports"
        self.REPORTS_DIR.mkdir(exist_ok=True)
        self.DATA_DIR = BASE_DIR / "data"
        self.DATA_DIR.mkdir(exist_ok=True)
        self.ASSETS_DIR = BASE_DIR / "assets"
        self.ASSETS_DIR.mkdir(exist_ok=True)
        self.STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
        self.STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    BUSINESS_OBJECTIVES = {
        "reduce_mttr_percent": 20,
        "increase_availability_percent": 5,
        "reduce_maintenance_cost_percent": 15,
    }

    MODEL_SUCCESS_CRITERIA = {
        "accuracy": 0.85,
        "recall": 0.90,
        "f1_score": 0.85,
        "inference_time_seconds": 1.0,
    }

    EQUIPMENT_TYPES = ["pala", "camion", "perforadora"]

    SENSOR_TYPES = [
        "temperatura",
        "presion_aceite",
        "rpm",
        "vibracion",
        "horas_operacion",
    ]

    ROLES = {
        "administrador": ["dashboard", "modelos", "reportes", "usuarios", "equipos", "entrenamiento", "prediccion", "admin"],
        "supervisor": ["dashboard", "modelos", "reportes", "equipos", "prediccion"],
        "operador": ["dashboard", "prediccion"],
        "analista": ["dashboard", "modelos", "reportes", "entrenamiento", "evaluacion", "prediccion"],
    }

settings = Settings()