import subprocess
import platform
import re
import socket
import json
import ipaddress
from typing import List, Dict
import os

class NetworkScanner:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), '../../config/settings.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {
                'network': {'subnet': '192.168.1.0/24', 'interface': 'auto'}
            }
        self.subnet = config['network'].get('subnet', '192.168.1.0/24')
        self.interface = config['network'].get('interface', 'auto')
        # Tworzymy obiekt sieci dla sprawdzania przynależności
        self.network = ipaddress.ip_network(self.subnet, strict=False)

    def get_hostname(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown"

    def get_vendor_from_mac(self, mac: str) -> str:
        oui = mac.replace(':', '').replace('-', '').upper()[:6]
        known_vendors = {
            '001122': 'TP-Link', '00163E': 'Xiaomi', '001D0F': 'Samsung',
            '0023CD': 'Apple', '000C29': 'VMware', '005056': 'VMware',
            '000D3A': 'Microsoft', '001E68': 'Intel', '3C970E': 'Wistron Info',
            '3CD92B': 'Hewlett Packard', '54EE75': 'Apple', '606BBD': 'Samsung',
            '74D435': 'Amazon Technologies', '7831C1': 'Apple', '784F43': 'Apple',
            '843835': 'Apple', 'A483E7': 'Microsoft', 'B827EB': 'Raspberry Pi',
            'DC7144': 'Samsung'
        }
        return known_vendors.get(oui, "Unknown")

    def is_valid_mac(self, mac: str) -> bool:
        """Sprawdza czy MAC jest prawidłowy (6 grup po 2 znaki hex)"""
        if not mac:
            return False
        clean_mac = mac.replace(':', '').replace('-', '').lower()
        if len(clean_mac) != 12:
            return False
        return bool(re.match(r'^[0-9a-f]{12}$', clean_mac))

    def is_in_local_network(self, ip: str) -> bool:
        """Sprawdza czy IP należy do lokalnej podsieci"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj in self.network
        except:
            return False

    def is_valid_device(self, ip: str, mac: str) -> bool:
        """Filtrowanie nieprawidłowych urządzeń"""
        if not self.is_valid_mac(mac):
            return False
        if not self.is_in_local_network(ip):
            return False
        # Pomijamy broadcast MAC
        if mac.lower() == 'ff:ff:ff:ff:ff:ff':
            return False
        # Pomijamy multicast (224.0.0.0 - 239.255.255.255)
        if ip.startswith('224.') or ip.startswith('239.'):
            return False
        # Pomijamy broadcast (255.255.255.255) i sieciowe .255
        if ip == '255.255.255.255' or ip.endswith('.255'):
            return False
        # Pomijamy APIPA (169.254.x.x)
        if ip.startswith('169.254.'):
            return False
        # Pomijamy localhost
        if ip == '127.0.0.1':
            return False
        return True

    def scan_arp(self) -> List[Dict]:
        devices = []
        try:
            system = platform.system()
            if system == "Windows":
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Używamy regex do poprawnego parsowania formatu Windows
                    pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F-]+)\s+'
                    for match in re.finditer(pattern, result.stdout):
                        ip = match.group(1)
                        mac = match.group(2).replace('-', ':').lower()

                        if self.is_valid_device(ip, mac):
                            devices.append({
                                'ip_address': ip,
                                'mac_address': mac,
                                'hostname': self.get_hostname(ip),
                                'vendor': self.get_vendor_from_mac(mac),
                                'source': 'arp'
                            })
            else:
                result = subprocess.run(['arp', '-an'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if not line.strip():
                            continue
                        match = re.search(r'\(([\d.]+)\) at ([a-fA-F0-9:]+)', line)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2)
                            if self.is_valid_device(ip, mac):
                                devices.append({
                                    'ip_address': ip,
                                    'mac_address': mac,
                                    'hostname': self.get_hostname(ip),
                                    'vendor': self.get_vendor_from_mac(mac),
                                    'source': 'arp'
                                })
        except Exception as e:
            print(f'ARP scan error: {e}')
        return devices

    def scan(self) -> List[Dict]:
        return self.scan_arp()

# ===== INSTANCJA SKANERA =====
scanner = NetworkScanner()