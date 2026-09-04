import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from src.db.connection import db_pool
from config.settings import settings

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expiration_hours = settings.JWT_EXPIRATION_HOURS
        self.bcrypt_rounds = settings.BCRYPT_ROUNDS
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def create_token(self, user_id: int, email: str, role: str) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def register_user(self, nombre: str, email: str, password: str, rol_id: int) -> Optional[int]:
        """Register a new user"""
        hashed_password = self.hash_password(password)
        query = """
            INSERT INTO usuarios (nombre, email, contrasena_hash, rol_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute(query, (nombre, email, hashed_password, rol_id))
                return cursor.fetchone()['id']
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
    
    def log_access_event(self, email: str, rol: str, accion: str, exitoso: bool = True, detalles: str = "", user_id: Optional[int] = None) -> bool:
        """Record entry in bitacora_accesos (audit log)"""
        try:
            query = """
                INSERT INTO bitacora_accesos (usuario_id, email, rol, accion, exitoso, detalles)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            with db_pool.get_cursor() as cursor:
                cursor.execute(query, (user_id, email, rol, accion, exitoso, detalles))
                return True
        except Exception as e:
            logger.warning(f"Could not log access event to DB: {e}")
            return False

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return token if successful"""
        query = """
            SELECT u.id, u.nombre, u.email, u.contrasena_hash, u.rol_id, u.activo, r.nombre as rol_nombre
            FROM usuarios u
            JOIN roles r ON r.id = u.rol_id
            WHERE u.email = %s AND u.activo = true
        """
        try:
            with db_pool.get_cursor() as cursor:
                cursor.execute(query, (email,))
                user = cursor.fetchone()
            
            if user and self.verify_password(password, user['contrasena_hash']):
                # Update last login
                with db_pool.get_cursor() as cursor:
                    cursor.execute(
                        "UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = %s",
                        (user['id'],)
                    )
                
                token = self.create_token(user['id'], user['email'], user['rol_nombre'])
                self.log_access_event(email, user['rol_nombre'], 'LOGIN', True, 'Autenticación exitosa', user['id'])
                return {
                    'user_id': user['id'],
                    'nombre': user['nombre'],
                    'email': user['email'],
                    'role': user['rol_nombre'],
                    'role_id': user['rol_id'],
                    'token': token
                }
            else:
                self.log_access_event(email, 'desconocido', 'LOGIN_FALLIDO', False, 'Credenciales inválidas')
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            self.log_access_event(email, 'desconocido', 'LOGIN_ERROR', False, f'Error: {e}')
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        query = """
            SELECT u.id, u.nombre, u.email, u.rol_id, u.activo, u.fecha_creacion, r.nombre as rol_nombre
            FROM usuarios u
            JOIN roles r ON r.id = u.rol_id
            WHERE u.id = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        query = """
            SELECT u.id, u.nombre, u.email, u.contrasena_hash, u.rol_id, u.activo, r.nombre as rol_nombre
            FROM usuarios u
            JOIN roles r ON r.id = u.rol_id
            WHERE u.email = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (email,))
            return cursor.fetchone()
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        hashed = self.hash_password(new_password)
        query = "UPDATE usuarios SET contrasena_hash = %s WHERE id = %s"
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (hashed, user_id))
            return cursor.rowcount > 0
    
    def create_reset_token(self, email: str) -> Optional[str]:
        """Create password reset token"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        reset_token = jwt.encode(
            {'user_id': user['id'], 'type': 'password_reset', 'exp': datetime.utcnow() + timedelta(hours=1)},
            self.secret_key,
            algorithm=self.algorithm
        )
        
        query = """
            UPDATE usuarios 
            SET reset_token = %s, reset_token_expira = %s 
            WHERE id = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (reset_token, datetime.utcnow() + timedelta(hours=1), user['id']))
        
        return reset_token
    
    def verify_reset_token(self, token: str) -> Optional[int]:
        """Verify password reset token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get('type') != 'password_reset':
                return None
            
            query = "SELECT id FROM usuarios WHERE id = %s AND reset_token = %s AND reset_token_expira > %s"
            with db_pool.get_cursor() as cursor:
                cursor.execute(query, (payload['user_id'], token, datetime.utcnow()))
                user = cursor.fetchone()
                return user['id'] if user else None
        except jwt.InvalidTokenError:
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token"""
        user_id = self.verify_reset_token(token)
        if not user_id:
            return False
        
        hashed = self.hash_password(new_password)
        query = """
            UPDATE usuarios 
            SET contrasena_hash = %s, reset_token = NULL, reset_token_expira = NULL
            WHERE id = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (hashed, user_id))
            return cursor.rowcount > 0
    
    def get_permissions(self, role_id: int) -> List[Dict[str, Any]]:
        """Get permissions for a role"""
        query = """
            SELECT recurso, accion, concedido
            FROM permisos
            WHERE rol_id = %s AND concedido = true
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (role_id,))
            return cursor.fetchall()
    
    def has_permission(self, role_id: int, resource: str, action: str) -> bool:
        """Check if role has specific permission"""
        query = """
            SELECT concedido FROM permisos
            WHERE rol_id = %s AND recurso = %s AND accion = %s
        """
        with db_pool.get_cursor() as cursor:
            cursor.execute(query, (role_id, resource, action))
            result = cursor.fetchone()
            return result and result['concedido'] if result else False

auth_service = AuthService()