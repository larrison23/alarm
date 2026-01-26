"""Class to connect to Homebridge API to update morning_switch in Homebridge Dummy plugin"""
import logging
import json
from datetime import datetime, timezone, timedelta
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

        logger.info("Attempting to login %s", url)

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.info("Login Successful. Token acquired")
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error("Login failed: %s", e)
            return None
    
    def _ensure_authenticated(self):
        if not self.token:
            logger.debug("No token found, authenticating...")
            self.login()
    
    def get_full_config(self):
        """Gets the current config block from homebridge dummy"""
        self._ensure_authenticated()
        url = f"{self.base_url}/api/config-editor/plugin/homebridge-dummy"

        try:
            logger.info("Fetching config from: %s", url)
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 401:
                logger.warning("Token expired. Re-authenticating...")
                self.login()
                response = requests.get(url, headers=self.headers, timeout=10)

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("Error fetching config: %s", e)
            return None
    
    def get_alarm_time(self):
        """Gets the current alarm time from homebridge dummy"""
        config_data = self.get_full_config()

        logger.debug("Config data (GET):\n%s", json.dumps(config_data, indent=4))

        if not config_data or not isinstance(config_data, list):
            logger.error("Config data not found.")
            return "12:01"

        try:
            accessories = config_data[0].get("accessories", [])
            morning_switch = next((acc for acc in accessories if acc["name"] == "morning_switch"), None)

            if not morning_switch:
                logger.error("morning_switch not found in config.")
                return "12:02"
            
            cron_str = morning_switch.get("schedule", {}).get("cronCustom", "0 12 * * *")
            parts = cron_str.split()

            minute = int(parts[0])
            hour_gmt = int(parts[1])

            gmt_time = datetime.now(timezone.utc).replace(hour=hour_gmt, minute=minute)
            local_time = gmt_time.astimezone()

            local_time += timedelta(minutes=6)

            return local_time.strftime("%H:%M")
        except (IndexError, KeyError, ValueError):
            logger.error("Cron job in Morning Switch not found")
            return "12:03"
    
    def update_morning_alarm(self, local_time_str):
        """
        Updates the alarm config in Homebridge UI
        
        :param self: Description
        :param local_time_str: Description
        """
        full_config = self.get_full_config()
        if not full_config:
            logger.error("Failed to retrieve config; cannot update alarm.")
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

        logger.debug("Config data (UPDATE):\n%s", json.dumps(full_config, indent=4))

        found = False
        for acc in full_config[0]["accessories"]:
            if acc["name"] == "morning_switch":
                acc["schedule"]["cronCustom"] = new_cron
                found = True
                logger.info("Updating cron job for morning_switch to: %s", new_cron)

        if found:
            url = f"{self.base_url}/api/config-editor/plugin/homebridge-dummy"
            res = requests.post(url, json=full_config, headers=self.headers, timeout=10)

            if not res.ok:
                logger.error("Config update failed: %d - %s", res.status_code, res.text)
                return False
            
            logger.info("Config updated successfully. Restarting Homebridge...")
            url_restart = f"{self.base_url}/api/server/restart/0E24DC719E2B"
            res_restart = requests.put(url_restart, headers=self.headers, timeout=10)
            return res_restart.ok
        logger.warning("morning_switch not found in configuration.")
        return False
    