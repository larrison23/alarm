"""Class to connect to Homebridge API to update morning_switch in Homebridge Dummy plugin"""
from datetime import datetime, timezone, timedelta
import requests

class HomebridgeClient:
    """Connects to the Homebridge API to update a switch in Homebridge Dummy plugin"""
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.headers = None
        self.token = None

    def login(self):
        """Authenticates with Swagger API"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": self.username, "password": self.password}

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        return self.token
    
    def _ensure_authenticated(self):
        if not self.token:
            self.login()
    
    def get_full_config(self):
        """Gets the current config block from homebridge dummy"""
        if not self.headers:
            self.login()
        url = f"{self.base_url}/api/config-editor/plugin/homebridge-dummy"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 401:
                self.login()
                response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching config: {e}")
            return None
    
    def get_alarm_time(self):
        """Gets the current alarm time from homebridge dummy"""
        config_data = self.get_full_config()

        if not config_data or not isinstance(config_data, list):
            return "12:00"

        try:
            accessories = config_data[0].get("accessories", [])
            morning_switch = next((acc for acc in accessories if acc["id"] == "morning_switch"), None)

            if not morning_switch:
                return "12:00"
            
            cron_str = morning_switch.get("schedule", {}).get("cronCustom", "0 12 * * *")
            parts = cron_str.split()

            minute = int(parts[0])
            hour_gmt = int(parts[1])

            gmt_time = datetime.now(timezone.utc).replace(hour=hour_gmt, minute=minute)
            local_time = gmt_time.astimezone()

            return local_time.strftime("%H:%M")
        except (IndexError, KeyError, ValueError):
            return "12:00"
    
    def update_morning_alarm(self, local_time_str):
        """
        Updates the alarm config in Homebridge UI
        
        :param self: Description
        :param local_time_str: Description
        """
        full_config = self.get_full_config()
        if not full_config:
            return False
        
        now = datetime.now().astimezone()
        local_dt = datetime.strptime(local_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=now.astimezone().tzinfo)
        
        if local_dt < now:
            local_dt += timedelta(days=1)

        local_dt -= timedelta(minutes=6)

        gmt_dt = local_dt.astimezone(timezone.utc)

        new_cron = f"{gmt_dt.minute} {gmt_dt.hour} * * *"

        full_config = self.get_full_config()

        found = False
        for acc in full_config[0]["accessories"]:
            if acc["id"] == "morning_switch":
                acc["schedule"]["cronCustom"] = new_cron
                found = True

        if found:
            url = f"{self.base_url}/api/config-editor/plugin/homebridge-dummy"
            res = requests.post(url, json=full_config, headers=self.headers, timeout=10)
            return res.ok
        return False
    