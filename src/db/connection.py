import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, min_conn=1, max_conn=10):
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(
                    min_conn, max_conn,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    cursor_factory=RealDictCursor
                )
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @contextmanager
    def get_connection(self):
        if self._pool is None:
            self.initialize()
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit=True):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def close_all(self):
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("Database connection pool closed")

db_pool = DatabasePool()

def get_db():
    """Dependency for FastAPI-style dependency injection"""
    return db_pool

def execute_query(query: str, params: tuple = None, fetch: bool = True):
    """Execute a query and return results"""
    with db_pool.get_cursor() as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None

def execute_single(query: str, params: tuple = None):
    """Execute query and return single result"""
    with db_pool.get_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()

def execute_insert(query: str, params: tuple = None):
    """Execute insert and return inserted ID"""
    with db_pool.get_cursor() as cursor:
        cursor.execute(query + " RETURNING id", params)
        return cursor.fetchone()['id']

def init_database():
    """Initialize database with schema"""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    with db_pool.get_cursor() as cursor:
        cursor.execute(schema)
    logger.info("Database schema initialized")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_pool.initialize()
    init_database()