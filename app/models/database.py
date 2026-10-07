<<<<<<< HEAD
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
=======
﻿from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
>>>>>>> f03f24f91d93894960a5c0cf84a19a331083b0ae
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
<<<<<<< HEAD

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(15), index=True)
    mac_address = Column(String(17), unique=True, index=True)
    hostname = Column(String(255))
    vendor = Column(String(100))
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_online = Column(Boolean, default=True)

class Traffic(Base):
    __tablename__ = "traffic"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)

class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    devices_found = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    alert_type = Column(String(50))
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "monitor.db")
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
=======
import json

try:
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f'Błąd wczytywania konfiguracji: {e}')
    config = {
        'database': {'path': 'monitor.db'},
        'network': {'subnet': '192.168.1.0/24', 'interface': 'auto', 'scan_interval': 300, 'traffic_interval': 60}
    }

DB_PATH = config['database'].get('path', 'monitor.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(15), unique=True, index=True)
    mac_address = Column(String(17), unique=True, index=True)
    hostname = Column(String(255))
    vendor = Column(String(255))
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    interface = Column(String(50))

class Traffic(Base):
    __tablename__ = 'traffic'
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    packets_sent = Column(Integer, default=0)
    packets_received = Column(Integer, default=0)

class ScanHistory(Base):
    __tablename__ = 'scan_history'
    id = Column(Integer, primary_key=True, index=True)
    scan_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    devices_found = Column(Integer, default=0)
    new_devices = Column(Integer, default=0)
    scan_type = Column(String(50))

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50))
    message = Column(Text)
    severity = Column(String(20), default='info')
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False)
    device_ip = Column(String(15))
    device_mac = Column(String(17))

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

if not os.path.exists(DB_PATH):
    Base.metadata.create_all(bind=engine)
>>>>>>> f03f24f91d93894960a5c0cf84a19a331083b0ae

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
<<<<<<< HEAD
        db.close()
=======
        db.close()
>>>>>>> f03f24f91d93894960a5c0cf84a19a331083b0ae
