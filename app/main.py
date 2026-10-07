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
from app.network.pinger import pinger
from app.network.speedtest import speed_tester
from app.models.database import PingResult, SpeedTest

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

@app.get("/stats", response_class=HTMLResponse)
async def read_stats(request: Request, db=Depends(get_db)):
    devices = db.query(Device).all()
    return templates.TemplateResponse("stats.html", {"request": request, "devices": devices})

@app.post("/api/ping/{device_id}")
async def api_ping_device(device_id: int, db=Depends(get_db)):
    device = db.query(Device).filter_by(id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    ping_data = pinger.ping_device(device.ip_address)
    new_ping = PingResult(
        device_id=device_id,
        packets_sent=ping_data["packets_sent"],
        packets_received=ping_data["packets_received"],
        packet_loss=ping_data["packet_loss"],
        avg_response_time=ping_data["avg_response_time"]
    )
    db.add(new_ping)
    db.commit()
    return JSONResponse(content={"device_id": device_id, "ping_data": ping_data})

@app.post("/api/speedtest")
async def api_speedtest(db=Depends(get_db)):
    test_data = speed_tester.run_test()
    new_test = SpeedTest(
        download_speed=test_data["download_speed"],
        upload_speed=test_data["upload_speed"],
        ping_latency=test_data["ping_latency"],
        server_name=test_data["server_name"],
        server_sponsor=test_data["server_sponsor"]
    )
    db.add(new_test)
    db.commit()
    return JSONResponse(content=test_data)

@app.get("/api/stats/ping/{device_id}")
async def api_ping_stats(device_id: int, db=Depends(get_db)):
    results = db.query(PingResult).filter_by(device_id=device_id).order_by(PingResult.timestamp.desc()).limit(50).all()
    return JSONResponse(content={
        "results": [{
            "timestamp": r.timestamp.isoformat(),
            "packet_loss": r.packet_loss,
            "avg_response_time": r.avg_response_time
        } for r in results]
    })

@app.get("/api/stats/speedtest")
async def api_speedtest_stats(db=Depends(get_db)):
    results = db.query(SpeedTest).order_by(SpeedTest.timestamp.desc()).limit(50).all()
    return JSONResponse(content={
        "results": [{
            "timestamp": r.timestamp.isoformat(),
            "download": r.download_speed,
            "upload": r.upload_speed,
            "ping": r.ping_latency
        } for r in results]
    })

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=False
    )