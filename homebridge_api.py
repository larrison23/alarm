import requests

class HomebridgeClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None

    def login(self):
        """Authenticates with Swagger API"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": self.username, "password": self.password}

        response = requests.post(url, json=payload)
        response.raise_for_status()
        self.token = response.json().get("access_token")
        return self.token