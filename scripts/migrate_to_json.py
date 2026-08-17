# -*- coding: utf-8 -*-
"""
Converte um artigo WordPress legado (index.html) para content/<slug>.json.

Uso:
    python3 scripts/migrate_to_json.py <slug> [<slug2> ...]
    python3 scripts/migrate_to_json.py --all

Depois de gerar o JSON, rode scripts/build_articles.py <slug> para
regenerar o index.html a partir dele.
"""
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")

CATEGORY_SLUG_MAP = {
    "saude": "saude-bucal",
    "saude-bucal": "saude-bucal",
    "ortodontia": "ortodontia",
    "tratamentos": "tratamentos",
    "gestantes": "gestantes",
    "curiosidades": "curiosidades",
}


def read(slug):
    path = os.path.join(ROOT, slug, "index.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


def get_meta(c, name):
    m = re.search(rf'<meta name="{name}" content="([^"]*)"', c)
    return m.group(1) if m else None


def get_title(c):
    m = re.search(r"<title>(.*?)</title>", c, re.S)
    return m.group(1).strip() if m else None


def get_h1(c):
    m = re.search(r'<h1 class="entry-title"[^>]*>(.*?)</h1>', c, re.S)
    if not m:
        return None
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()


def get_category(c):
    m = re.search(r'ast-terms-link"><a href="[^"]*\?cat=([a-z-]+)"', c)
    if m:
        return CATEGORY_SLUG_MAP.get(m.group(1), "saude-bucal")
    return "saude-bucal"


def get_hero_image(c):
    m = re.search(
        r'<div class="post-thumb-img-content post-thumb"><img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/><noscript><img[^>]*srcset="([^"]*)"',
        c,
    )
    if m:
        return {"url": m.group(1), "alt": m.group(2), "srcset": m.group(3)}
    # fallback: og:image only
    og = re.search(r'property="og:image" content="([^"]*)"', c)
    if og:
        url = og.group(1)
        return {"url": url, "alt": "", "srcset": f"{url} 1024w"}
    return None


def get_dates(c):
    pub = re.search(r'"datePublished":"([^"]*)"', c)
    mod = re.search(r'"dateModified":"([^"]*)"', c)
    pub_date = pub.group(1)[:10] if pub else "2025-01-01"
    mod_date = mod.group(1)[:10] if mod else pub_date
    return pub_date, mod_date


def get_entry_content(c):
    start_marker = re.search(r'<div class="entry-content clear"[^>]*>', c)
    if not start_marker:
        raise ValueError("entry-content nao encontrado")
    start = start_marker.end()
    end = c.index('</div><!-- .entry-content .clear -->', start)
    return c[start:end]


def normalize_inline(html):
    """Limpa espacos/format do WP mas mantem tags inline (strong, a, em)."""
    html = html.strip()
    html = re.sub(r"\s+", " ", html)
    return html


def parse_blocks(entry_html, slug):
    blocks = []

    # Extrai a secao de FAQ separadamente (heading "Perguntas Frequentes"),
    # com ou sem <strong> em volta do texto (inconsistente entre artigos),
    # e independente da classe do <h2> (Gutenberg, Elementor ou editor classico)
    faq_match = re.search(
        r'<h2[^>]*>(?:<span[^>]*>)?(?:<strong>)?((?:\d+\.\s*)?Perguntas Frequentes[^<]*?)(?:</strong>)?(?:</span>)?:?</h2>(.*?)(?=<h2[^>]*>|\Z)',
        entry_html,
        re.S,
    )
    faq_html = None
    faq_title = None
    if faq_match:
        faq_title = normalize_inline(faq_match.group(1)).rstrip(":").strip()
        faq_html = faq_match.group(2)
        entry_html = entry_html[: faq_match.start()] + entry_html[faq_match.end():]

    # Author bio box (se ja padronizado) - remove, o template gera de novo
    entry_html = re.sub(r'<hr style="margin:40px 0.*?</div>\s*(?=</div>|\Z)', "", entry_html, flags=re.S)

    # Tokeniza em ordem: h2, h3, ul/ol, p, figure/img
    pattern = re.compile(
        r'<h2(?: class="wp-block-heading")?>(?:<strong>)?(.*?)(?:</strong>)?</h2>'
        r'|<h3(?: class="wp-block-heading")?>(?:<strong>)?(.*?)(?:</strong>)?</h3>'
        r'|<(ul|ol)(?: class="wp-block-list")?>(.*?)</\3>'
        r'|<figure[^>]*class="wp-block-table[^"]*"[^>]*>\s*<table[^>]*>(.*?)</table>\s*</figure>'
        r'|<p(?: class="wp-block-paragraph")?>(.*?)</p>'
        r'|<figure[^>]*class="wp-block-image[^"]*"[^>]*>.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"'
        r'|<h[4-6][^>]*>(.*?)</h[4-6]>',
        re.S,
    )

    for m in pattern.finditer(entry_html):
        if m.group(1) is not None:
            blocks.append({"tipo": "titulo", "nivel": 2, "texto": normalize_inline(m.group(1))})
        elif m.group(2) is not None:
            blocks.append({"tipo": "titulo", "nivel": 3, "texto": normalize_inline(m.group(2))})
        elif m.group(3) is not None:
            itens = re.findall(r"<li[^>]*>(.*?)</li>", m.group(4), re.S)
            blocks.append({"tipo": "lista", "itens": [normalize_inline(i) for i in itens]})
        elif m.group(5) is not None:
            linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(5), re.S)
            tabela = []
            for linha in linhas:
                celulas = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", linha, re.S)
                tabela.append([normalize_inline(c) for c in celulas])
            blocks.append({"tipo": "tabela", "linhas": tabela})
        elif m.group(6) is not None:
            texto = normalize_inline(m.group(6))
            if texto:
                blocks.append({"tipo": "paragrafo", "texto": texto})
        elif m.group(7) is not None:
            blocks.append({"tipo": "imagem", "url": m.group(7), "alt": m.group(8)})
        elif m.group(9) is not None:
            # h4-h6 usados como texto estilizado (Elementor), nao como heading semantico
            texto = normalize_inline(m.group(9))
            if texto:
                blocks.append({"tipo": "paragrafo", "texto": texto})

    # Fallback generico: alguns artigos antigos (editor classico do WP ou
    # Elementor) nao usam as classes wp-block-*. Se nada foi extraido pelo
    # parser especifico acima, tenta de novo so por nome de tag.
    if not blocks:
        generic_pattern = re.compile(
            r'<h2[^>]*>(.*?)</h2>'
            r'|<h3[^>]*>(.*?)</h3>'
            r'|<(ul|ol)[^>]*>(.*?)</\3>'
            r'|<table[^>]*>(.*?)</table>'
            r'|<p[^>]*>(.*?)</p>',
            re.S,
        )
        for m in generic_pattern.finditer(entry_html):
            if m.group(1) is not None:
                texto = normalize_inline(re.sub(r"<[^>]+>", "", m.group(1)))
                if texto:
                    blocks.append({"tipo": "titulo", "nivel": 2, "texto": texto})
            elif m.group(2) is not None:
                texto = normalize_inline(re.sub(r"<[^>]+>", "", m.group(2)))
                if texto:
                    blocks.append({"tipo": "titulo", "nivel": 3, "texto": texto})
            elif m.group(4) is not None:
                itens = re.findall(r"<li[^>]*>(.*?)</li>", m.group(4), re.S)
                itens = [normalize_inline(i) for i in itens]
                if itens:
                    blocks.append({"tipo": "lista", "itens": itens})
            elif m.group(5) is not None:
                linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(5), re.S)
                tabela = []
                for linha in linhas:
                    celulas = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", linha, re.S)
                    tabela.append([normalize_inline(c) for c in celulas])
                if tabela:
                    blocks.append({"tipo": "tabela", "linhas": tabela})
            elif m.group(6) is not None:
                raw = m.group(6)
                img_m = re.search(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"', raw)
                if img_m and len(re.sub(r"<[^>]+>", "", raw).strip()) < 5:
                    # paragrafo que so contem uma imagem -> vira bloco de imagem
                    blocks.append({"tipo": "imagem", "url": img_m.group(1), "alt": img_m.group(2)})
                    continue
                texto = normalize_inline(raw)
                if texto:
                    blocks.append({"tipo": "paragrafo", "texto": texto})

    if faq_html:
        perguntas = []
        qa_pattern = re.compile(
            r'<h3[^>]*>(?:<strong>)?(.*?)(?:</strong>)?</h3>\s*<p[^>]*>(.*?)</p>',
            re.S,
        )
        emoji_num = re.compile(r"^[0-9]️?⃣\s*|^\d+\.\s*")
        emoji_check = re.compile(r"^[✅\U0001F6AB]\s*")
        for qm in qa_pattern.finditer(faq_html):
            q = emoji_num.sub("", normalize_inline(qm.group(1))).strip()
            a = re.sub(r"<[^>]+>", "", qm.group(2))
            a = emoji_check.sub("", normalize_inline(a)).strip()
            perguntas.append({"pergunta": q, "resposta": a})
        if perguntas:
            blocks.append({"tipo": "faq", "titulo": faq_title or "Perguntas Frequentes", "perguntas": perguntas})

    return blocks


def migrate(slug):
    c = read(slug)

    titulo_meta = get_title(c)
    meta_description = get_meta(c, "description")
    h1 = get_h1(c) or titulo_meta
    categoria = get_category(c)
    hero = get_hero_image(c)
    pub_date, mod_date = get_dates(c)
    entry_html = get_entry_content(c)
    blocks = parse_blocks(entry_html, slug)

    if not blocks:
        raise ValueError(f"Nenhum bloco extraido para {slug} - verificar manualmente")

    article = {
        "slug": slug,
        "titulo_meta": titulo_meta,
        "titulo_h1": h1,
        "meta_description": meta_description,
        "categoria": categoria,
        "autor": "dra-kesya-nogueira",
        "cluster_pai": None,
        "capa": {
            "url": hero["url"] if hero else "",
            "srcset": hero.get("srcset", "") if hero else "",
            "og": f"https://stelleodontologia.com.br{hero['url']}" if hero and hero["url"].startswith("/") else (hero["url"] if hero else ""),
            "alt": hero["alt"] if hero else "",
        },
        "publicado": True,
        "publicado_em": pub_date,
        "atualizado_em": mod_date,
        "blocos": blocks,
    }

    out_path = os.path.join(CONTENT_DIR, f"{slug}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)

    return out_path, len(blocks)


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python3 scripts/migrate_to_json.py <slug> [<slug2> ...]")
        sys.exit(1)

    for slug in args:
        try:
            path, n = migrate(slug)
            print(f"OK   {slug:60s} {n:3d} blocos -> {os.path.relpath(path, ROOT)}")
        except Exception as e:
            print(f"FAIL {slug:60s} {e}")


if __name__ == "__main__":
    main()
