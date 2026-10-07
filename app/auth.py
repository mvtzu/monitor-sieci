from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import json
import ipaddress

# Wczytanie ustawień
try:
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f'Błąd wczytywania konfiguracji: {e}')
    config = {
        'auth': {
            'users': [{'username': 'admin', 'password_hash': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'}],
            'whitelist_ips': ['127.0.0.1']
        }
    }

# Kontekst hashowania haseł
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
security = HTTPBasic()
WHITELIST_IPS = config['auth'].get('whitelist_ips', ['127.0.0.1'])

class AuthHandler:
    def __init__(self):
        self.users = {}
        for user in config['auth'].get('users', []):
            self.users[user['username']] = user['password_hash']

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def authenticate_user(self, username: str, password: str) -> bool:
        if username not in self.users:
            return False
        return self.verify_password(password, self.users[username])

    def is_ip_whitelisted(self, ip: str) -> bool:
        try:
            if ip in ['localhost', '127.0.0.1', '::1']:
                return True
            if ip in WHITELIST_IPS:
                return True
            for net in WHITELIST_IPS:
                try:
                    if '/' in net:
                        network = ipaddress.ip_network(net, strict=False)
                        if ipaddress.ip_address(ip) in network:
                            return True
                except:
                    pass
            return False
        except:
            return False

auth_handler = AuthHandler()

async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    request: Request = None
) -> dict:
    client_ip = request.client.host if request else ''
    if auth_handler.is_ip_whitelisted(client_ip):
        return {'username': 'whitelisted', 'auth_method': 'ip'}
    if not auth_handler.authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Nieprawidłowa nazwa użytkownika lub hasło',
            headers={'WWW-Authenticate': 'Basic'},
        )
    return {'username': credentials.username, 'auth_method': 'basic'}