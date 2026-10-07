import speedtest
from typing import Dict
from app.models.database import SpeedTest

class SpeedTester:
    def __init__(self):
        self.s = speedtest.Speedtest()

    def run_test(self) -> Dict:
        """Uruchamia speed test i zwraca wyniki"""
        try:
            self.s.get_best_server()
            self.s.download()
            self.s.upload()
            results = self.s.results.dict()

            return {
                "download_speed": round(results["download"] / 1_000_000, 2),
                "upload_speed": round(results["upload"] / 1_000_000, 2),
                "ping_latency": results["ping"],
                "server_name": results["server"]["name"],
                "server_sponsor": results["server"]["sponsor"],
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "download_speed": 0.0,
                "upload_speed": 0.0,
                "ping_latency": 0.0,
                "server_name": "Unknown",
                "server_sponsor": "Unknown",
                "success": False,
                "error": str(e)
            }

speed_tester = SpeedTester()