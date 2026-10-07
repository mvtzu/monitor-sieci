from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os

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

class PingResult(Base):
    __tablename__ = "ping_results"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    packets_sent = Column(Integer, default=4)
    packets_received = Column(Integer, default=0)
    packet_loss = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)

class SpeedTest(Base):
    __tablename__ = "speed_tests"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    download_speed = Column(Float, default=0.0)
    upload_speed = Column(Float, default=0.0)
    ping_latency = Column(Float, default=0.0)
    server_name = Column(String(255))
    server_sponsor = Column(String(255))

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "monitor.db")
engine = create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()