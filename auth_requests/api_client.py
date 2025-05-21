import requests
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.token_expires_at = None
        self.jsessionid = None
        self._token_refresh_thread = None
        self._stop_refresh = threading.Event()

    def authenticate(self):
        print("Iniciando autenticação...")
        url = "https://api.energisa.io/oauth/access-token"
        headers = {
            "Authorization": os.getenv("ENERGISA_AUTH_HEADER"),
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
        print(f"Autenticação concluída. Access Token: {self.token}")
        print(f"Token expira em: {expires_in} segundos")

    def login(self):
        print("Realizando login...")
        url = "https://dev-api.energisa.io/sankhya/v1/login?outputType=json"
        headers = {
            "Content-Type": "application/json",
            "client_id": os.getenv("ENERGISA_CLIENT_ID"),
            "access_token": self.token
        }
        payload = {
            "serviceName": "MobileLoginSP.login",
            "requestBody": {
                "NOMUSU": {"$": os.getenv("LOGIN_NOMUSU")},
                "INTERNO": {"$": os.getenv("LOGIN_INTERNO")},
                "KEEPCONNECTED": {"$": "S"}
            }
        }
        response = self.session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        self.jsessionid = response.cookies.get("JSESSIONID")
        print(f"Login realizado com sucesso. JSESSIONID: {self.jsessionid}")
        return response.json()

    def start_token_auto_refresh(self, interval_seconds=120):
        if self._token_refresh_thread and self._token_refresh_thread.is_alive():
            print("Thread de renovação de token já está rodando.")
            return

        print(f"Iniciando thread de renovação de token a cada {interval_seconds} segundos...")

        def refresh_loop():
            while not self._stop_refresh.is_set():
                # Troca sleep por wait, que é interrompível!
                self._stop_refresh.wait(interval_seconds)
                if self._stop_refresh.is_set():
                    break
                try:
                    print("\nRenovando token de acesso automaticamente...")
                    self.authenticate()
                    self.login()
                    print("Token e sessão renovados com sucesso.\n")
                except Exception as e:
                    print(f"Erro ao renovar token automaticamente: {e}")

        self._token_refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._token_refresh_thread.start()

    def stop_token_auto_refresh(self):
        self._stop_refresh.set()
        if self._token_refresh_thread:
            self._token_refresh_thread.join()

    def consulta_prospect(self, cpf_cnpj):
        print(f"Consultando Prospect para CPF/CNPJ: {cpf_cnpj} ...")
        url = "https://dev-api.energisa.io/sankhya/v1/loadrecords?outputType=json"
        headers = {
            "Content-Type": "application/json",
            "client_id": os.getenv("ENERGISA_CLIENT_ID"),
            "access_token": self.token
        }
        cookies = {"JSESSIONID": self.jsessionid} if self.jsessionid else None
        payload = {
            "serviceName": "CRUDServiceProvider.loadRecords",
            "requestBody": {
                "dataSet": {
                    "rootEntity": "ParceiroProspect",
                    "includePresentationFields": "N",
                    "offsetPage": "0",
                    "criteria": {
                        "expression": {
                            "$": f"this.CGC_CPF = '{cpf_cnpj}'"
                        }
                    },
                    "entity": {
                        "fieldset": {
                            "list": "CODPAP,NOMEPAP,CGC_CPF,TIPPESSOA,CODVEND,ESTADOCIVIL"
                        }
                    }
                }
            }
        }
        response = self.session.post(url, headers=headers, json=payload, cookies=cookies)
        try:
            data = response.json()
            print(f"Resposta da consulta: {data}")
            f0 = data["responseBody"]["entities"]["entity"]["f0"]["$"]
            print(f"Prospect (CODPAP) encontrado para {cpf_cnpj}: {f0}")
            return f0, ""
        except Exception as e:
            print(f"Nenhum Prospect encontrado para {cpf_cnpj}. Erro: {e}")
            try:
                msg = data.get('statusMessage', str(e))
            except:
                msg = str(e)
            return "", f"Erro em Prospect: {msg}"

    def consulta_negociacao(self, codpap):
        print(f"Consultando mumero_negociacao para CODPAP: {codpap} ...")
        url = "https://dev-api.energisa.io/sankhya/v1/loadrecords?outputType=json"
        headers = {
            "Content-Type": "application/json",
            "client_id": os.getenv("ENERGISA_CLIENT_ID"),
            "access_token": self.token
        }
        cookies = {"JSESSIONID": self.jsessionid} if self.jsessionid else None
        payload = {
            "serviceName": "CRUDServiceProvider.loadRecords",
            "requestBody": {
                "dataSet": {
                    "rootEntity": "OrdemServico",
                    "includePresentationFields": "N",
                    "offsetPage": "0",
                    "criteria": {
                        "expression": {
                            "$": f"this.CODPAP = {codpap}"
                        }
                    },
                    "entity": {
                        "fieldset": {
                            "list": "CODPAP,CODVEND,CODCONTATOPAP,SITUACAO,CODMETOD"
                        }
                    }
                }
            }
        }
        response = self.session.post(url, headers=headers, json=payload, cookies=cookies)
        try:
            data = response.json()
            print(f"Resposta da consulta: {data}")
            entities = data["responseBody"]["entities"]["entity"]
            if isinstance(entities, list) and entities:
                f5 = entities[0].get("f5", {}).get("$", "")
            elif isinstance(entities, dict):
                f5 = entities.get("f5", {}).get("$", "")
            else:
                f5 = ""
            print(f"mumero_negociacao (f5) encontrado para CODPAP {codpap}: {f5}")
            return f5, ""
        except Exception as e:
            print(f"Nenhuma mumero_negociacao encontrada para CODPAP {codpap}. Erro: {e}")
            try:
                msg = data.get('statusMessage', str(e))
            except:
                msg = str(e)
            return "", f"Erro em mumero_negociacao: {msg}"

    def consulta_numero_instalacao(self, codpap):
        print(f"Consultando numero_instalacao para CODPAP: {codpap} ...")
        url = "https://dev-api.energisa.io/sankhya/v1/loadrecords?outputType=json"
        headers = {
            "Content-Type": "application/json",
            "client_id": os.getenv("ENERGISA_CLIENT_ID"),
            "access_token": self.token
        }
        cookies = {"JSESSIONID": self.jsessionid} if self.jsessionid else None
        payload = {
            "serviceName": "CRUDServiceProvider.loadRecords",
            "requestBody": {
                "dataSet": {
                    "rootEntity": "AD_INSTPROSP",
                    "includePresentationFields": "N",
                    "offsetPage": "0",
                    "criteria": {
                        "expression": {
                            "$": f"this.CODPAP = {codpap}"
                        }
                    },
                    "entity": {
                        "fieldset": {
                            "list": "CODPAP,NROUNICO,ATIVO,NROINSTALACAO,CODDISTRIBUIDORA"
                        }
                    }
                }
            }
        }
        response = self.session.post(url, headers=headers, json=payload, cookies=cookies)
        try:
            data = response.json()
            print(f"Resposta da consulta: {data}")
            entities = data["responseBody"]["entities"]["entity"]
            if isinstance(entities, list):
                nros = [item.get("f3", {}).get("$", "") for item in entities if "f3" in item and item.get("f3", {}).get("$", "")]
                numero_instalacao = ";".join(nros)
            elif isinstance(entities, dict):
                numero_instalacao = entities.get("f3", {}).get("$", "")
            else:
                numero_instalacao = ""
            print(f"numero_instalacao encontrado para CODPAP {codpap}: {numero_instalacao}")
            return numero_instalacao, ""
        except Exception as e:
            print(f"Nenhum numero_instalacao encontrada para CODPAP {codpap}. Erro: {e}")
            try:
                msg = data.get('statusMessage', str(e))
            except:
                msg = str(e)
            return "", f"Erro em numero_instalacao: {msg}"