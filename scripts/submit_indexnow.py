# -*- coding: utf-8 -*-
"""
Envia URLs para o IndexNow (Bing, Yandex) para pedir indexacao/rastreamento
imediato, em vez de esperar o crawler passar por conta propria.

Uso:
    python3 scripts/submit_indexnow.py bruxismo-e-medicamentos clareamento-caseiro-ou-consultorio
        -> envia so essas URLs especificas (rodar apos publicar/editar artigos)

    python3 scripts/submit_indexnow.py --all
        -> envia todas as URLs do sitemap.xml (usar so na configuracao inicial,
           ou apos mudancas grandes - nao precisa rodar toda hora)

Documentacao do protocolo: https://www.indexnow.org/
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
BASE_URL = "https://stelleodontologia.com.br"
HOST = "stelleodontologia.com.br"

KEY_FILE = "5f87b33d767d3a87236550467e8c220b.txt"
KEY = KEY_FILE.replace(".txt", "")
KEY_LOCATION = f"{BASE_URL}/{KEY_FILE}"

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def load_all_sitemap_urls():
    with open(SITEMAP_PATH, encoding="utf-8") as f:
        text = f.read()
    return re.findall(r"<loc>([^<]+)</loc>", text)


def slugs_to_urls(slugs):
    return [f"{BASE_URL}/{slug.strip('/')}/" for slug in slugs]


def submit(url_list):
    if not url_list:
        print("Nada para enviar.")
        return

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": url_list,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"OK - status {resp.status} - {len(url_list)} URL(s) enviada(s)")
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"ERRO: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 scripts/submit_indexnow.py <slug1> <slug2> ... | --all")
        sys.exit(1)

    if args == ["--all"]:
        urls = load_all_sitemap_urls()
        print(f"Enviando todas as {len(urls)} URLs do sitemap...")
        submit(urls)
    else:
        urls = slugs_to_urls(args)
        print(f"Enviando {len(urls)} URL(s):")
        for u in urls:
            print(" -", u)
        submit(urls)
