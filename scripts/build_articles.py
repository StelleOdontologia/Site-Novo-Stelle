# -*- coding: utf-8 -*-
"""
Gera os index.html dos artigos a partir dos JSONs em content/*.json
e do template em templates/artigo.html.

Uso:
    python3 scripts/build_articles.py            # builda tudo
    python3 scripts/build_articles.py bruxismo    # builda so um slug

Fonte da verdade = content/*.json. Nunca edite os index.html gerados
diretamente - edite o JSON e rode este script de novo.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "artigo.html")
BASE_URL = "https://stelleodontologia.com.br"

with open(os.path.join(CONTENT_DIR, "categorias.json"), encoding="utf-8") as f:
    CATEGORIAS = json.load(f)
CATEGORIAS_BY_ID = {c["id"]: c for c in CATEGORIAS}

with open(os.path.join(CONTENT_DIR, "autores.json"), encoding="utf-8") as f:
    AUTORES = json.load(f)


def esc(s):
    """Escapa aspas duplas para uso dentro de atributos HTML."""
    return s.replace('"', "&quot;")


def render_bloco(bloco, article):
    tipo = bloco["tipo"]

    if tipo == "paragrafo":
        return f'<p class="wp-block-paragraph">{bloco["texto"]}</p>'

    if tipo == "titulo":
        nivel = bloco.get("nivel", 2)
        return f'<h{nivel}>{bloco["texto"]}</h{nivel}>'

    if tipo == "lista":
        itens = "".join(f"<li>{item}</li>" for item in bloco["itens"])
        return f"<ul>{itens}</ul>"

    if tipo == "tabela":
        linhas = bloco["linhas"]
        html = ['<table class="article-table">']
        if linhas:
            head, *rest = linhas
            html.append("<tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>")
            for linha in rest:
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>")
        html.append("</table>")
        return "\n".join(html)

    if tipo == "imagem":
        alt = esc(bloco["alt"])
        return f'<img class="article-inline-img" loading="lazy" src="{bloco["url"]}" alt="{alt}">'

    if tipo == "callout":
        return (
            '<div class="article-cta-box">'
            f'<p><strong>{bloco["texto"]}</strong></p>'
            f'<a href="{bloco["cta_link"]}" target="_blank" rel="noopener">{bloco["cta_texto"]}</a>'
            "</div>"
        )

    if tipo == "pillar_badge":
        return f'<a href="{bloco["link"]}" class="article-pillar-badge">📖 {bloco["texto"]}</a>'

    if tipo == "faq":
        titulo = bloco.get("titulo", "Perguntas Frequentes")
        html = [f"<h2>{titulo}</h2>"]
        for qa in bloco["perguntas"]:
            html.append(f'<h3>{qa["pergunta"]}</h3>')
            html.append(f'<p>{qa["resposta"]}</p>')
        return "\n\n".join(html)

    raise ValueError(f"Tipo de bloco desconhecido: {tipo}")


def strip_tags(html):
    return re.sub(r"<[^>]+>", " ", html)


def build_faq_schema(blocos):
    for b in blocos:
        if b["tipo"] == "faq":
            return {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": strip_tags(qa["pergunta"]).strip(),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": strip_tags(qa["resposta"]).strip(),
                        },
                    }
                    for qa in b["perguntas"]
                ],
            }
    return None


def build_article_schema(article):
    slug = article["slug"]
    url = f"{BASE_URL}/{slug}/"
    autor = AUTORES[article["autor"]]

    breadcrumb_items = [
        {"@type": "ListItem", "position": 1, "item": {"@id": BASE_URL, "name": "Início"}},
        {"@type": "ListItem", "position": 2, "item": {"@id": f"{BASE_URL}/blog/", "name": "Blog"}},
    ]
    pos = 3
    if article.get("cluster_pai"):
        pai_url = f"{BASE_URL}/{article['cluster_pai']}/"
        breadcrumb_items.append(
            {"@type": "ListItem", "position": pos, "item": {"@id": pai_url, "name": article["cluster_pai"].replace("-", " ").title()}}
        )
        pos += 1
    breadcrumb_items.append(
        {"@type": "ListItem", "position": pos, "item": {"@id": url, "name": article["titulo_h1"]}}
    )

    graph = [
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": breadcrumb_items,
        },
        {
            "@type": "Person",
            "@id": autor["url"],
            "name": autor["nome"],
            "url": autor["url"],
            "jobTitle": autor["cargo"],
        },
    ]

    blog_posting = {
        "@type": "BlogPosting",
        "@id": f"{url}#richSnippet",
        "headline": article["titulo_h1"],
        "name": article["titulo_h1"],
        "description": article["meta_description"],
        "keywords": article["slug"].replace("-", " "),
        "datePublished": f'{article["publicado_em"]}T09:00:00-03:00',
        "dateModified": f'{article["atualizado_em"]}T09:00:00-03:00',
        "author": {"@id": autor["url"]},
        "publisher": {"@id": f"{BASE_URL}/#organization"},
        "image": article["capa"]["og"],
        "mainEntityOfPage": url,
    }
    if article.get("cluster_pai"):
        blog_posting["isPartOf"] = {"@id": f"{BASE_URL}/{article['cluster_pai']}/"}
    if article.get("cluster_filhos"):
        blog_posting["hasPart"] = [
            {
                "@type": "BlogPosting",
                "headline": _load_article(filho)["titulo_h1"],
                "url": f"{BASE_URL}/{filho}/",
            }
            for filho in article["cluster_filhos"]
        ]
    graph.append(blog_posting)

    faq_schema = build_faq_schema(article["blocos"])
    if faq_schema:
        graph.append(faq_schema)

    return {"@context": "https://schema.org", "@graph": graph}


_article_cache = {}


def _load_article(slug):
    if slug not in _article_cache:
        with open(os.path.join(CONTENT_DIR, f"{slug}.json"), encoding="utf-8") as f:
            _article_cache[slug] = json.load(f)
    return _article_cache[slug]


_all_articles_sorted = None


def _thumb_url(article):
    """Pega a menor imagem do srcset (geralmente 300w) para usar como miniatura."""
    srcset = article["capa"].get("srcset", "")
    candidates = []
    for part in srcset.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.rsplit(" ", 1)
        if len(bits) == 2 and bits[1].endswith("w"):
            try:
                candidates.append((int(bits[1][:-1]), bits[0]))
            except ValueError:
                continue
    if candidates:
        candidates.sort(key=lambda c: c[0])
        return candidates[0][1]
    return article["capa"]["url"]


def get_all_articles_sorted():
    """Todos os artigos publicados, do mais recente para o mais antigo."""
    global _all_articles_sorted
    if _all_articles_sorted is not None:
        return _all_articles_sorted
    slugs = [
        os.path.splitext(f)[0]
        for f in os.listdir(CONTENT_DIR)
        if f.endswith(".json") and f not in ("categorias.json", "autores.json")
    ]
    articles = [_load_article(s) for s in slugs]
    articles = [a for a in articles if a.get("publicado", True)]
    articles.sort(key=lambda a: max(a["publicado_em"], a["atualizado_em"]), reverse=True)
    _all_articles_sorted = articles
    return articles


def build_prev_next_html(article):
    all_articles = get_all_articles_sorted()
    slugs_in_order = [a["slug"] for a in all_articles]
    idx = slugs_in_order.index(article["slug"])

    newer = all_articles[idx - 1] if idx > 0 else None
    older = all_articles[idx + 1] if idx < len(all_articles) - 1 else None

    if not newer and not older:
        return ""

    def card(a, label, extra_class):
        thumb = _thumb_url(a)
        return (
            f'<a href="/{a["slug"]}/" class="{extra_class}">'
            f'<img src="{thumb}" alt="" loading="lazy">'
            '<span class="article-nav-body">'
            f'<span class="article-nav-label">{label}</span>'
            f'<span class="article-nav-title">{a["titulo_h1"]}</span>'
            "</span></a>"
        )

    html = ['<div class="article-nav-links">']
    html.append(card(older, "← Artigo anterior", "article-nav-prev") if older else "<span></span>")
    html.append(card(newer, "Próximo artigo →", "article-nav-next") if newer else "<span></span>")
    html.append("</div>")
    return "\n".join(html)


def build_breadcrumb_html(article):
    parts = ['<a href="/">Início</a>', '<a href="/blog/">Blog</a>']
    if article.get("cluster_pai"):
        pai = _load_article(article["cluster_pai"])
        parts.append(f'<a href="/{article["cluster_pai"]}/">{pai["titulo_h1"].split(":")[0]}</a>')
    parts.append(article["titulo_h1"].split(":")[0])
    return " &gt; ".join(parts)


def build_category_buttons_html(active_id):
    buttons = []
    for cat in CATEGORIAS:
        cls = "category-btn active" if cat["id"] == active_id else "category-btn"
        buttons.append(
            f'<a href="{cat["url"]}" class="{cls}">{cat["nome"]} <span class="count">{cat["count"]}</span></a>'
        )
    return "\n      ".join(buttons)


def build_author_box_html(article):
    autor = AUTORES[article["autor"]]
    return (
        '<hr style="margin:40px 0;border:none;border-top:2px solid #e0e0e0;">\n'
        '<div class="author-box">\n'
        f'  <img src="{autor["foto"]}" alt="{esc(autor["nome"])} - {esc(autor["cargo"])}">\n'
        "  <div>\n"
        f'    <h3>{autor["nome"]}</h3>\n'
        f'    <p><strong>{autor["cro"]}</strong> &bull; {autor["cargo"]}</p>\n'
        f'    <p>{autor["bio"]}</p>\n'
        "  </div>\n"
        "</div>"
    )


def build_article(slug):
    article = _load_article(slug)
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    body_html = "\n\n".join(render_bloco(b, article) for b in article["blocos"])
    schema_json = json.dumps(build_article_schema(article), ensure_ascii=False)

    pillar_badge_html = ""
    for b in article["blocos"]:
        if b["tipo"] == "pillar_badge":
            pillar_badge_html = render_bloco(b, article)
            break

    replacements = {
        "{{SLUG}}": slug,
        "{{TITLE_META}}": article["titulo_meta"],
        "{{META_DESCRIPTION}}": article["meta_description"],
        "{{CANONICAL_URL}}": f"{BASE_URL}/{slug}/",
        "{{OG_IMAGE}}": article["capa"]["og"],
        "{{SCHEMA_JSON}}": schema_json,
        "{{BREADCRUMB_HTML}}": build_breadcrumb_html(article),
        "{{CATEGORY_BUTTONS_HTML}}": build_category_buttons_html(article["categoria"]),
        "{{PILLAR_BADGE_HTML}}": pillar_badge_html,
        "{{H1}}": article["titulo_h1"],
        "{{HERO_IMG_SRC}}": article["capa"]["url"],
        "{{HERO_IMG_SRCSET}}": article["capa"]["srcset"],
        "{{HERO_IMG_ALT}}": esc(article["capa"]["alt"]),
        "{{BODY_HTML}}": body_html,
        "{{AUTHOR_BOX_HTML}}": build_author_box_html(article),
        "{{PREV_NEXT_HTML}}": build_prev_next_html(article),
    }

    html = template
    for token, value in replacements.items():
        html = html.replace(token, value)

    assert "{{" not in html, f"Sobrou placeholder nao substituido em {slug}: " + re.search(r"\{\{[^}]*\}\}", html).group(0)

    out_dir = os.path.join(ROOT, slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_path, len(article["blocos"])


def main():
    slugs = sys.argv[1:]
    if not slugs:
        slugs = [
            os.path.splitext(f)[0]
            for f in os.listdir(CONTENT_DIR)
            if f.endswith(".json") and f not in ("categorias.json", "autores.json")
        ]

    for slug in slugs:
        path, n_blocos = build_article(slug)
        print(f"OK  {slug:30s} {n_blocos:3d} blocos -> {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
