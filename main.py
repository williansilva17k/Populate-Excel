import pandas as pd
import requests
import os

# Parâmetros fixos
API_URL = "https://dev-api.energisa.io/sankhya/v1/loadrecords?outputType=json"
CLIENT_ID = "58754a81-01b2-4fa8-91fb-425823f5c731"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Pegue do seu login/flow
JSESSIONID = os.getenv("JSESSIONID")      # Pegue do seu login/flow

def request_api(payload):
    headers = {
        "Content-Type": "application/json",
        "client_id": CLIENT_ID,
        "access_token": ACCESS_TOKEN
    }
    cookies = {}
    if JSESSIONID:
        cookies["JSESSIONID"] = JSESSIONID
    resp = requests.post(API_URL, headers=headers, json=payload, cookies=cookies)
    resp.raise_for_status()
    return resp.json()

def get_prospect(cpf_cnpj):
    payload = {
        "serviceName": "CRUDServiceProvider.loadRecords",
        "requestBody": {
            "dataSet": {
                "rootEntity": "ParceiroProspect",
                "includePresentationFields": "N",
                "offsetPage": "0",
                "criteria": {"expression": {"$": f"this.CGC_CPF = '{cpf_cnpj}'"}},
                "entity": {"fieldset": {"list": "CODPAP,NOMEPAP,CGC_CPF,TIPPESSOA,CODVEND,ESTADOCIVIL"}}
            }
        }
    }
    data = request_api(payload)
    try:
        return data["responseBody"]["entities"]["entity"]["f0"]["$"]
    except Exception:
        return ""

def get_mumero_negociacao(codpap):
    payload = {
        "serviceName": "CRUDServiceProvider.loadRecords",
        "requestBody": {
            "dataSet": {
                "rootEntity": "OrdemServico",
                "includePresentationFields": "N",
                "offsetPage": "0",
                "criteria": {"expression": {"$": f"this.CODPAP = {codpap}"}},
                "entity": {"fieldset": {"list": "CODPAP,CODVEND,CODCONTATOPAP,SITUACAO,CODMETOD,NUMOS"}}
            }
        }
    }
    data = request_api(payload)
    try:
        entities = data["responseBody"]["entities"]["entity"]
        if isinstance(entities, list):
            return entities[0]["f5"]["$"]
        else:
            return entities["f5"]["$"]
    except Exception:
        return ""

def get_numero_instalacao(codpap):
    payload = {
        "serviceName": "CRUDServiceProvider.loadRecords",
        "requestBody": {
            "dataSet": {
                "rootEntity": "AD_INSTPROSP",
                "includePresentationFields": "N",
                "offsetPage": "0",
                "criteria": {"expression": {"$": f"this.CODPAP = {codpap}"}},
                "entity": {"fieldset": {"list": "CODPAP,NROUNICO,ATIVO,NROINSTALACAO,CODDISTRIBUIDORA"}}
            }
        }
    }
    data = request_api(payload)
    try:
        entities = data["responseBody"]["entities"]["entity"]
        if isinstance(entities, list):
            return ";".join(ent["f3"]["$"] for ent in entities if ent.get("f3", {}).get("$"))
        else:
            return entities["f3"]["$"]
    except Exception:
        return ""

def main():
    df = pd.read_excel("Assets.xlsx", dtype=str)
    for idx, row in df.iterrows():
        cpf_cnpj = row.get("CPF_CNPJ")
        if not cpf_cnpj:
            continue
        prospect = get_prospect(cpf_cnpj)
        df.at[idx, "Prospect"] = prospect
        if prospect:
            mumero_negociacao = get_mumero_negociacao(prospect)
            df.at[idx, "mumero_negociacao"] = mumero_negociacao
            numero_instalacao = get_numero_instalacao(prospect)
            df.at[idx, "numero_instalacao"] = numero_instalacao

    df.to_excel("output.xlsx", index=False)

if __name__ == "__main__":
    main()