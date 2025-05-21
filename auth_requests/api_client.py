import requests
import time

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.token_expires_at = None

    def authenticate(self):
        """Autentica usando client_credentials e armazena o access_token e expiração."""
        url = "https://api.energisa.io/oauth/access-token"
        headers = {
            "Authorization": "Basic NTg3NTRhODEtMDFiMi00ZmE4LTkxZmItNDI1ODIzZjVjNzMxOmQ3MmRlYWE2LTg1NWQtNGQ2ZC04NTYzLWY2MWI0ZTZkMWJmZA==",
            "Content-Type": "application/json",
        }
        payload = {
            "grant_type": "client_credentials"
        }
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        self.token = data.get("access_token")
        expires_in = data.get("expires_in", 0)
        self.token_expires_at = time.time() + expires_in
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        print(f"Access Token: {self.token}")
        print(f"Token expira em: {expires_in} segundos")

    # Stubs para futuras implementações:
    def login(self):
        pass

    def consulta_1(self, params):
        pass

    def consulta_2(self, params):
        pass

    def consulta_3(self, params):
        pass