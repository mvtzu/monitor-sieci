import nmap
import socket
import subprocess
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
import json
import os
import netifaces

try:
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f'Błąd wczytywania konfiguracji: {e}')
    config = {
        'network': {'subnet': '192.168.1.0/24', 'interface': 'auto'}
    }

class NetworkScanner:
    def __init__(self):
        self.subnet = config['network'].get('subnet', '192.168.1.0/24')
        self.interface = config['network'].get('interface', 'auto')
        try:
            self.nm = nmap.PortScanner()
        except:
            self.nm = None

    def get_local_ip(self) -> str:
        try:
            if self.interface and self.interface != 'auto':
                addrs = netifaces.ifaddresses(self.interface)
                if netifaces.AF_INET in addrs:
                    return addrs[netifaces.AF_INET][0]['addr']
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    if not ip.startswith('127.'):
                        return ip
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception as e:
            print(f'Błąd pobierania lokalnego IP: {e}')
            return '127.0.0.1'

    def get_network_info(self) -> Dict:
        try:
            local_ip = self.get_local_ip()
            if '/' in self.subnet:
                network = self.subnet
            else:
                ip_parts = local_ip.split('.')
                network = f'{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24'
            return {
                'local_ip': local_ip,
                'subnet': network,
                'interface': self.interface,
                'gateway': self.get_default_gateway()
            }
        except Exception as e:
            print(f'Błąd pobierania informacji o sieci: {e}')
            return {
                'local_ip': '127.0.0.1',
                'subnet': '127.0.0.0/24',
                'interface': 'lo',
                'gateway': None
            }

    def get_default_gateway(self) -> Optional[str]:
        try:
            gateways = netifaces.gateways()
            if netifaces.default in gateways and gateways[netifaces.default]:
                return gateways[netifaces.default][netifaces.AF_INET][0]
            return None
        except:
            return None

    def scan_arp(self) -> List[Dict]:
        devices = []
        try:
            try:
                result = subprocess.run(
                    ['arp', '-a'],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        match = re.search(r'\(([\d.]+)\) at ([a-fA-F0-9:]+)', line)
                        if match:
                            ip = match.group(1)
                            mac = match.group(2)
                            hostname = self.get_hostname(ip)
                            devices.append({
                                'ip_address': ip,
                                'mac_address': mac,
                                'hostname': hostname,
                                'vendor': self.get_vendor_from_mac(mac),
                                'source': 'arp',
                                'timestamp': datetime.now(timezone.utc).isoformat()
                            })
            except Exception as e:
                print(f'Błąd skanowania ARP: {e}')
            return devices
        except Exception as e:
            print(f'Błąd skanowania ARP: {e}')
            return devices

    def scan_nmap(self, subnet: str = None) -> List[Dict]:
        devices = []
        try:
            if not self.nm:
                print('nmap nie jest dostępny')
                return self.scan_arp()
            if subnet is None:
                subnet = self.subnet
            self.nm.scan(hosts=subnet, arguments='-sn')
            for host in self.nm.all_hosts():
                if host in self.nm[host].all_hosts():
                    host_data = self.nm[host]
                    mac_address = None
                    vendor = None
                    if 'mac' in host_data:
                        mac_address = host_data['mac']
                        vendor = host_data['addresses'].get('mac', '')
                    hostname = host_data.hostname() if host_data.hostname() else None
                    os_info = None
                    if 'osmatch' in host_data:
                        os_info = host_data['osmatch'][0]['name'] if host_data['osmatch'] else None
                    devices.append({
                        'ip_address': host,
                        'mac_address': mac_address,
                        'hostname': hostname,
                        'vendor': vendor,
                        'os': os_info,
                        'source': 'nmap',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'status': host_data.state()
                    })
            return devices
        except Exception as e:
            print(f'Błąd skanowania nmap: {e}')
            return self.scan_arp()

    def scan_full(self) -> List[Dict]:
        arp_devices = self.scan_arp()
        if not arp_devices:
            return self.scan_nmap()
        nmap_devices = self.scan_nmap()
        combined = []
        arp_ips = {d['ip_address'] for d in arp_devices if d.get('ip_address')}
        nmap_ips = {d['ip_address'] for d in nmap_devices if d.get('ip_address')}
        for arp_device in arp_devices:
            combined_device = arp_device.copy()
            for nmap_device in nmap_devices:
                if nmap_device.get('ip_address') == arp_device.get('ip_address'):
                    if nmap_device.get('hostname') and not combined_device.get('hostname'):
                        combined_device['hostname'] = nmap_device['hostname']
                    if nmap_device.get('os') and not combined_device.get('os'):
                        combined_device['os'] = nmap_device['os']
                    if nmap_device.get('status'):
                        combined_device['status'] = nmap_device['status']
                    break
            combined.append(combined_device)
        for nmap_device in nmap_devices:
            if nmap_device.get('ip_address') not in arp_ips:
                combined.append(nmap_device)
        return combined

    def get_hostname(self, ip: str) -> Optional[str]:
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            return None

    def get_vendor_from_mac(self, mac: str) -> str:
        try:
            if mac:
                oui = mac.replace(':', '').upper()[:6]
                known_vendors = {
                    '00163E': 'Xensource',
                    '005056': 'VMware',
                    '000C29': 'VMware',
                    'B827EB': 'Raspberry Pi',
                    'DC7144': 'Samsung Electronics',
                    'A44C81': 'Xiaomi',
                    '74D02B': 'Amazon Technologies',
                    '54EE75': 'Apple',
                    '606BBD': 'Samsung Electronics',
                }
                return known_vendors.get(oui, f'Unknown ({oui})')
            return 'Unknown'
        except:
            return 'Unknown'

    def ping_device(self, ip: str, count: int = 1) -> bool:
        try:
            result = subprocess.run(
                ['ping', '-n', str(count), ip],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def check_port(self, ip: str, port: int, timeout: int = 1) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False

scanner = NetworkScanner()
