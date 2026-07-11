#!/usr/bin/env python3
"""
Indexação automática via Google Indexing API
Stelle Odontologia — stelleodontologia.com.br

Uso:
  python indexar_urls.py               # indexa todas as URLs novas do sitemap
  python indexar_urls.py --todas       # força re-indexação de todas as URLs
  python indexar_urls.py --url <URL>   # indexa uma URL específica

Requisitos:
  pip install google-auth google-auth-httplib2 requests

Setup:
  1. Coloque o arquivo JSON da conta de serviço em:
     scripts/credenciais-google.json
  2. Adicione a conta de serviço como Proprietário no GSC:
     index-stelle-odontologia@index-stelle-odontologia.iam.gserviceaccount.com
"""

import json
import os
import sys
import argparse
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Configuração ──────────────────────────────────────────────────────────────
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credenciais-google.json")
SITEMAP_URL      = "https://stelleodontologia.com.br/sitemap.xml"
LOG_FILE         = os.path.join(os.path.dirname(__file__), "indexacao-log.json")
SCOPES           = ["https://www.googleapis.com/auth/indexing"]

# ── Autenticação ──────────────────────────────────────────────────────────────
def get_access_token():
    from google.oauth2 import service_account
    import google.auth.transport.requests
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

# ── Sitemap ───────────────────────────────────────────────────────────────────
def buscar_urls_sitemap():
    resp = requests.get(SITEMAP_URL, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall("sm:url/sm:loc", ns)]

# ── Log de URLs já indexadas ──────────────────────────────────────────────────
def carregar_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_log(log):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

# ── Indexing API ──────────────────────────────────────────────────────────────
def indexar_url(token, url):
    resp = requests.post(
        "https://indexing.googleapis.com/v3/urlNotifications:publish",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"url": url, "type": "URL_UPDATED"},
        timeout=30,
    )
    return resp.status_code, resp.json()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Indexação automática GSC — Stelle")
    parser.add_argument("--todas",  action="store_true", help="Re-indexa todas as URLs do sitemap")
    parser.add_argument("--url",    type=str,            help="Indexa uma URL específica")
    args = parser.parse_args()

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERRO: Arquivo de credenciais nao encontrado: {CREDENTIALS_FILE}")
        print("      Mova o JSON baixado do Google Cloud para esse caminho.")
        sys.exit(1)

    print("Obtendo token de acesso...")
    token = get_access_token()

    log = carregar_log()
    hoje = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.url:
        urls = [args.url]
    else:
        print(f"Buscando URLs em {SITEMAP_URL}...")
        urls = buscar_urls_sitemap()
        print(f"  {len(urls)} URLs encontradas no sitemap.")
        if not args.todas:
            urls_novas = [u for u in urls if u not in log]
            print(f"  {len(urls_novas)} URLs novas (nao indexadas ainda).")
            urls = urls_novas

    if not urls:
        print("OK: Nenhuma URL nova para indexar.")
        return

    print(f"\nIndexando {len(urls)} URL(s)...\n")
    sucesso = 0
    for url in urls:
        status, resp = indexar_url(token, url)
        if status == 200:
            print(f"  [OK]   {url}")
            log[url] = {"indexado_em": hoje, "status": "ok"}
            sucesso += 1
        else:
            erro = resp.get("error", {}).get("message", str(resp))
            print(f"  [ERRO] {url}")
            print(f"         {erro}")
            log[url] = {"indexado_em": hoje, "status": "erro", "detalhe": erro}

    salvar_log(log)
    print(f"\nResultado: {sucesso}/{len(urls)} indexadas com sucesso.")
    print(f"Log salvo em: {LOG_FILE}")

if __name__ == "__main__":
    main()
