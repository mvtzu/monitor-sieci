import psutil 
from datetime import datetime, timezone 
 
class TrafficMonitor: 
    def __init__(self): 
        self.last_stats = {} 
 
    def get_network_stats(self): 
        stats = {} 
        try: 
            net_io = psutil.net_io_counters(pernic=True) 
            for interface, data in net_io.items(): 
                stats[interface] = { 
                    'bytes_sent': data.bytes_sent, 
                    'bytes_recv': data.bytes_recv, 
                    'packets_sent': data.packets_sent, 
                    'packets_recv': data.packets_recv 
                } 
        except Exception as e: 
            print(f'Traffic stats error: {e}') 
        return stats 
 
traffic_monitor = TrafficMonitor() 
