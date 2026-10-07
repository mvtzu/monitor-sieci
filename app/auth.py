from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
from typing import Optional
import json
import os

class AuthHandler:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '../config/settings.json')
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {
                "auth": {
                    "users": [{"username": "admin", "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"}],
                    "whitelist_ips": ["127.0.0.1", "::1"]
                }
            }
        self.users = {u["username"]: u["password_hash"] for u in config["auth"]["users"]}
        self.whitelist_ips = config["auth"]["whitelist_ips"]
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBasic()

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self.pwd_context.verify(plain, hashed)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def is_ip_whitelisted(self, ip: str) -> bool:
        return ip in self.whitelist_ips

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        if username not in self.users:
            return None
        if not self.verify_password(password, self.users[username]):
            return None
        return username

    def get_current_user(self, credentials: HTTPBasicCredentials = Depends(HTTPBasic()), request: Request = None):
        if not self.is_ip_whitelisted(request.client.host):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="IP not whitelisted",
                headers={"WWW-Authenticate": "Basic"},
            )
        username = self.authenticate_user(credentials.username, credentials.password)
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return username

auth_handler = AuthHandler()
get_current_user = auth_handler.get_current_user