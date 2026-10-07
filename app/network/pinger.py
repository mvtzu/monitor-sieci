from pythonping import ping
from datetime import datetime, timezone
from typing import Dict
from app.models.database import PingResult

class NetworkPinger:
    def __init__(self):
        pass

    def ping_device(self, ip: str, count: int = 4) -> Dict:
        """Pinguje urządzenie i zwraca statystyki"""
        try:
            response = ping(ip, count=count, timeout=1)
            packets_received = len([r for r in response._responses if r.success])
            packets_sent = count
            packet_loss = ((packets_sent - packets_received) / packets_sent) * 100 if packets_sent > 0 else 100.0

            total_time = sum([r.time_elapsed * 1000 for r in response._responses if r.success])
            avg_time = total_time / packets_received if packets_received > 0 else 0.0

            return {
                "ip": ip,
                "packets_sent": packets_sent,
                "packets_received": packets_received,
                "packet_loss": round(packet_loss, 2),
                "avg_response_time": round(avg_time, 2),
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "ip": ip,
                "packets_sent": count,
                "packets_received": 0,
                "packet_loss": 100.0,
                "avg_response_time": 0.0,
                "success": False,
                "error": str(e)
            }

pinger = NetworkPinger()