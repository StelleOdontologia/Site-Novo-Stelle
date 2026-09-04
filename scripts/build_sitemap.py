# -*- coding: utf-8 -*-
"""
Gera o sitemap.xml a partir de content/*.json (artigos do blog) mais
uma lista fixa de paginas institucionais (nao JSON-driven).

Uso:
    python3 scripts/build_sitemap.py

Fonte da verdade dos artigos = content/*.json (mesmo campo "publicado"
usado por build_articles.py). Nunca edite o sitemap.xml gerado
diretamente - edite este script ou os JSONs e rode de novo.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
BASE_URL = "https://stelleodontologia.com.br"

# Paginas institucionais fixas (nao geradas a partir de content/*.json).
# (path, changefreq, priority)
STATIC_PAGES = [
    ("/", "monthly", "1.0"),
    ("/sobre/", "monthly", "0.8"),
    ("/alinhadores/", "monthly", "0.9"),
    ("/implantes/", "monthly", "0.9"),
    ("/clareamento-dental/", "monthly", "0.8"),
    ("/protese-dentaria/", "monthly", "0.8"),
    ("/toxina-botulinica/", "monthly", "0.8"),
    ("/endodontia/", "monthly", "0.8"),
    ("/ortodontia-miofuncional/", "monthly", "0.8"),
    ("/contato/", "yearly", "0.7"),
    ("/blog/", "weekly", "0.9"),
]


def load_articles():
    articles = []
    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".json"):
            continue
        if fname in ("categorias.json", "autores.json"):
            continue
        with open(os.path.join(CONTENT_DIR, fname), encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("publicado", True):
            continue
        articles.append(data)
    return articles


def priority_for(article):
    """Pilares (com cluster_filhos) tem prioridade maior; satelites (com
    cluster_pai) prioridade menor; artigos avulsos ficam no meio."""
    if article.get("cluster_filhos"):
        return "0.8"
    if article.get("cluster_pai"):
        return "0.6"
    return "0.7"


def build_sitemap():
    articles = load_articles()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "",
        "  <!-- Páginas principais -->",
    ]

    for path, changefreq, priority in STATIC_PAGES:
        lines.append(
            f'  <url><loc>{BASE_URL}{path}</loc>'
            f'<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>'
        )

    lines.append("")
    lines.append("  <!-- Artigos do blog -->")

    for article in sorted(articles, key=lambda a: a["slug"]):
        slug = article["slug"]
        priority = priority_for(article)
        lastmod = article.get("atualizado_em") or article.get("publicado_em")
        lastmod_tag = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        lines.append(
            f'  <url><loc>{BASE_URL}/{slug}/</loc>{lastmod_tag}'
            f'<changefreq>yearly</changefreq><priority>{priority}</priority></url>'
        )

    lines.append("")
    lines.append("</urlset>")
    lines.append("")

    with open(SITEMAP_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print(f"OK - sitemap.xml gerado com {len(STATIC_PAGES)} paginas institucionais + {len(articles)} artigos")


if __name__ == "__main__":
    build_sitemap()
