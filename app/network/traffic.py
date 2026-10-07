import psutil
import socket
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import json
import netifaces

try:
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f'Błąd wczytywania konfiguracji: {e}')
    config = {
        'network': {'interface': 'auto'}
    }

class TrafficMonitor:
    def __init__(self):
        self.interface = config['network'].get('interface', 'auto')
        self.last_stats = {}

    def get_active_connections(self) -> List[Dict]:
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED':
                    connections.append({
                        'local_ip': conn.laddr.ip if conn.laddr else None,
                        'local_port': conn.laddr.port if conn.laddr else None,
                        'remote_ip': conn.raddr.ip if conn.raddr else None,
                        'remote_port': conn.raddr.port if conn.raddr else None,
                        'status': conn.status,
                        'pid': conn.pid,
                        'protocol': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                    })
        except Exception as e:
            print(f'Błąd pobierania połączeń: {e}')
        return connections

    def get_network_stats(self) -> Dict:
        stats = {}
        try:
            net_io = psutil.net_io_counters(pernic=True)
            for interface, data in net_io.items():
                stats[interface] = {
                    'bytes_sent': data.bytes_sent,
                    'bytes_recv': data.bytes_recv,
                    'packets_sent': data.packets_sent,
                    'packets_recv': data.packets_recv,
                }
        except Exception as e:
            print(f'Błąd pobierania statystyk sieci: {e}')
        return stats

    def get_interface_stats(self, interface: str = None) -> Dict:
        if interface is None:
            interface = self.interface if self.interface != 'auto' else self.get_default_interface()
        try:
            net_io = psutil.net_io_counters(pernic=True)
            if interface in net_io:
                data = net_io[interface]
                return {
                    'interface': interface,
                    'bytes_sent': data.bytes_sent,
                    'bytes_recv': data.bytes_recv,
                    'packets_sent': data.packets_sent,
                    'packets_recv': data.packets_recv,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            return {'interface': interface, 'error': 'Interface not found'}
        except Exception as e:
            return {'interface': interface, 'error': str(e)}

    def get_default_interface(self) -> str:
        try:
            gateways = netifaces.gateways()
            if netifaces.default in gateways and gateways[netifaces.default]:
                return gateways[netifaces.default][netifaces.AF_INET][1]
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    return interface
            return 'eth0'
        except:
            return 'eth0'

    def get_traffic_diff(self, interface: str = None) -> Dict:
        if interface is None:
            interface = self.interface if self.interface != 'auto' else self.get_default_interface()
        current_stats = self.get_interface_stats(interface)
        if interface not in self.last_stats:
            self.last_stats[interface] = current_stats
            return {
                'interface': interface,
                'bytes_sent_diff': 0,
                'bytes_recv_diff': 0,
                'packets_sent_diff': 0,
                'packets_recv_diff': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        last = self.last_stats[interface]
        diff = {
            'interface': interface,
            'bytes_sent_diff': current_stats['bytes_sent'] - last['bytes_sent'],
            'bytes_recv_diff': current_stats['bytes_recv'] - last['bytes_recv'],
            'packets_sent_diff': current_stats['packets_sent'] - last['packets_sent'],
            'packets_recv_diff': current_stats['packets_recv'] - last['packets_recv'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self.last_stats[interface] = current_stats
        return diff

traffic_monitor = TrafficMonitor()
