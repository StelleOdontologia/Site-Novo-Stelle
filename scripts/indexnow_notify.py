# -*- coding: utf-8 -*-
"""
Notifica o IndexNow (Bing e buscadores compatíveis) sobre paginas alteradas
no deploy atual. Chamado pelo workflow .github/workflows/indexnow.yml
apos cada deploy de producao bem-sucedido na Vercel.

Uso:
    python3 scripts/indexnow_notify.py <sha_anterior> <sha_atual>
"""
import json
import subprocess
import sys
import urllib.request

HOST = "stelleodontologia.com.br"
BASE_URL = f"https://{HOST}"
INDEXNOW_KEY = "5b53ec2db74605fa413e333407481fa8"
KEY_LOCATION = f"{BASE_URL}/{INDEXNOW_KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def changed_files(sha_antes, sha_depois):
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", sha_antes, sha_depois],
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"AVISO: git diff falhou ({e}); nada a notificar.")
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def file_to_url(path):
    if path == "sitemap.xml":
        return f"{BASE_URL}/sitemap.xml"
    if path.endswith("/index.html"):
        slug = path[: -len("/index.html")]
        return f"{BASE_URL}/{slug}/"
    if path == "index.html":
        return f"{BASE_URL}/"
    return None


def build_url_list(files):
    urls = []
    for f in files:
        url = file_to_url(f)
        if url and url not in urls:
            urls.append(url)
    return urls


def notify(urls):
    if not urls:
        print("Nenhuma pagina publica alterada; nada a notificar.")
        return

    payload = {
        "host": HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"IndexNow OK - status {resp.status} - {len(urls)} URLs: {urls}")
    except Exception as e:
        print(f"AVISO: falha ao notificar IndexNow ({e}); ignorando.")


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 scripts/indexnow_notify.py <sha_anterior> <sha_atual>")
        return
    sha_antes, sha_depois = sys.argv[1], sys.argv[2]
    files = changed_files(sha_antes, sha_depois)
    urls = build_url_list(files)
    notify(urls)


if __name__ == "__main__":
    main()
