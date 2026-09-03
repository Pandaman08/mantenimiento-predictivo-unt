import jwt

from src.auth.auth_service import AuthService


def test_password_hash_and_verify():
    service = AuthService()
    password = 'Secret123!'
    hashed = service.hash_password(password)
    assert hashed != password
    assert service.verify_password(password, hashed) is True
    assert service.verify_password('wrong', hashed) is False


def test_jwt_round_trip():
    service = AuthService()
    token = service.create_token(user_id=7, email='demo@unt.edu.pe', role='analista')
    payload = service.decode_token(token)
    assert payload is not None
    assert payload['user_id'] == 7
    assert payload['email'] == 'demo@unt.edu.pe'
    assert payload['role'] == 'analista'
