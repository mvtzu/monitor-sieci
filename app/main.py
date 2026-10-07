import uvicorn
import json
import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.models.database import Base, get_db, Device, Traffic, ScanHistory, Alert, User, engine
from app.auth import get_current_user, AuthHandler
from app.network.scanner import scanner
from app.network.traffic import TrafficMonitor

# === TWORZENIE TABLI W BAZIE DANYCH ===
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Monitor Sieci Domowej")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

config_path = os.path.join(os.path.dirname(__file__), '../config/settings.json')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
except:
    config = {
        "network": {"subnet": "192.168.1.0/24", "interface": "auto", "scan_interval": 300, "traffic_interval": 60},
        "auth": {"users": [{"username": "admin", "password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"}], "whitelist_ips": ["127.0.0.1", "::1"]},
        "database": {"path": "monitor.db"},
        "server": {"host": "0.0.0.0", "port": 8000, "debug": True}
    }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/devices", response_class=HTMLResponse)
async def read_devices(request: Request, db=Depends(get_db)):
    devices = db.query(Device).all()
    return templates.TemplateResponse("devices.html", {"request": request, "devices": devices})

@app.get("/api/devices")
async def api_get_devices(db=Depends(get_db)):
    devices = db.query(Device).all()
    return JSONResponse(content={
        "devices": [{
            "id": d.id,
            "ip_address": d.ip_address,
            "mac_address": d.mac_address,
            "hostname": d.hostname,
            "vendor": d.vendor,
            "first_seen": d.first_seen.isoformat() if d.first_seen else None,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "is_online": d.is_online
        } for d in devices]
    })

@app.post("/api/scan")
async def api_scan(db=Depends(get_db)):
    devices = scanner.scan()
    for device in devices:
        # Normalizujemy MAC do małych liter
        normalized_mac = device['mac_address'].lower()

        existing = db.query(Device).filter_by(mac_address=normalized_mac).first()
        now = datetime.now(timezone.utc)

        if existing:
            existing.ip_address = device['ip_address']
            existing.hostname = device['hostname']
            existing.vendor = device['vendor']
            existing.last_seen = now
            existing.is_online = True
        else:
            new_device = Device(
                ip_address=device['ip_address'],
                mac_address=normalized_mac,  # Zapisujemy znormalizowany MAC
                hostname=device['hostname'],
                vendor=device['vendor'],
                first_seen=now,
                last_seen=now,
                is_online=True
            )
            db.add(new_device)
    db.commit()
    return JSONResponse(content={"message": "Scan completed", "devices_found": len(devices)})

@app.get("/api/system/status")
async def api_system_status():
    return JSONResponse(content={"status": "running", "timestamp": datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=False
    )