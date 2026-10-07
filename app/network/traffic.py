import psutil
import time
from datetime import datetime, timezone
from typing import Dict, List
import socket

class TrafficMonitor:
    def __init__(self):
        self.previous_stats = {}

    def get_network_stats(self) -> Dict:
        """Pobiera statystyki ruchu sieciowego"""
        stats = {}
        net_io = psutil.net_io_counters(pernic=True)

        for interface, io in net_io.items():
            stats[interface] = {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
                "timestamp": datetime.now(timezone.utc)
            }
        return stats

    def get_traffic_diff(self, interface: str = None) -> Dict:
        """Oblicza różnicę w ruchu sieciowym od ostatniego pomiaru"""
        current_stats = self.get_network_stats()
        diff = {}

        for iface, current in current_stats.items():
            if interface and iface != interface:
                continue

            previous = self.previous_stats.get(iface, {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0,
                "timestamp": datetime.now(timezone.utc)
            })

            time_diff = (current["timestamp"] - previous["timestamp"]).total_seconds()
            if time_diff <= 0:
                time_diff = 1

            diff[iface] = {
                "bytes_sent_per_sec": (current["bytes_sent"] - previous["bytes_sent"]) / time_diff,
                "bytes_recv_per_sec": (current["bytes_recv"] - previous["bytes_recv"]) / time_diff,
                "packets_sent_per_sec": (current["packets_sent"] - previous["packets_sent"]) / time_diff,
                "packets_recv_per_sec": (current["packets_recv"] - previous["packets_recv"]) / time_diff,
                "total_bytes": current["bytes_sent"] + current["bytes_recv"]
            }

        self.previous_stats = current_stats
        return diff

traffic_monitor = TrafficMonitor()