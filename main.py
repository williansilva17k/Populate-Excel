import sys
import pandas as pd
from auth_requests.api_client import APIClient

def main():
    input_path = "Assets.xlsx"
    output_path = "output.xlsx"

    print("Iniciando processo de integração...")
    client = APIClient()
    client.authenticate()
    client.login()
    client.start_token_auto_refresh(interval_seconds=200)

    print("Lendo planilha de entrada...")
    df = pd.read_excel(input_path, dtype=str, engine="openpyxl")
    for col in ["Prospect", "mumero_negociacao", "numero_instalacao", "Erro_Integracao"]:
        if col not in df.columns:
            df[col] = ""

    for i, row in df.iterrows():
        print(f"\nProcessando linha {i+1} - Asset_ID: {row.get('Asset_ID', '')}")
        erro = ""
        codpap = ""
        mumero_negociacao = ""
        cpf_cnpj = row.get("CPF_CNPJ", "")
        if pd.notna(cpf_cnpj) and cpf_cnpj.strip():
            codpap, erro_prospect = client.consulta_prospect(cpf_cnpj)
            df.at[i, "Prospect"] = codpap
            erro += erro_prospect
            if codpap:
                mumero_negociacao, erro_negoc = client.consulta_negociacao(codpap)
                df.at[i, "mumero_negociacao"] = mumero_negociacao
                erro += erro_negoc
                numero_instalacao, erro_inst = client.consulta_numero_instalacao(codpap)
                df.at[i, "numero_instalacao"] = numero_instalacao
                erro += erro_inst
            else:
                df.at[i, "mumero_negociacao"] = ""
                df.at[i, "numero_instalacao"] = ""
        else:
            erro = "CPF_CNPJ não informado"
            df.at[i, "Prospect"] = ""
            df.at[i, "mumero_negociacao"] = ""
            df.at[i, "numero_instalacao"] = ""
        df.at[i, "Erro_Integracao"] = erro

    print("\nSalvando planilha de saída...")
    df.to_excel(output_path, index=False)
    print(f"Processo finalizado! Planilha salva como: {output_path}")

    client.stop_token_auto_refresh()
    sys.exit(0)

if __name__ == "__main__":
    main()