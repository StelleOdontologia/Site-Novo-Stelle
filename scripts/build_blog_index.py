# -*- coding: utf-8 -*-
"""
Gera a grade de cards e os contadores do filtro em blog/index.html a
partir de content/*.json - fonte unica da verdade, sem datas nem
contagens digitadas a mao.

Uso:
    python3 scripts/build_blog_index.py
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_articles as ba

ROOT = ba.ROOT
BLOG_INDEX_PATH = os.path.join(ROOT, "blog", "index.html")

MESES = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
}

# categoria.json usa "saude-bucal", mas os cards do blog usam a classe/slug "saude"
CAT_SLUG_MAP = {"saude-bucal": "saude"}

CAT_LABELS = {c["id"]: c["nome"] for c in ba.CATEGORIAS if c["id"] != "blog"}


def format_date(iso_date):
    y, m, d = (int(x) for x in iso_date.split("-"))
    return f"{d} {MESES[m]} {y}"


def build_card_html(article):
    slug = article["slug"]
    cat_id = article["categoria"]
    cat_slug = CAT_SLUG_MAP.get(cat_id, cat_id)
    cat_label = CAT_LABELS.get(cat_id, cat_id.title())
    thumb = ba._thumb_url(article)
    date_display = format_date(max(article["publicado_em"], article["atualizado_em"]))
    excerpt = article["meta_description"]

    return (
        f'    <a href="/{slug}/" class="blog-card cat-{cat_slug}" data-cat="{cat_slug}">\n'
        f'      <div class="blog-card-thumb"><img src="{thumb}" alt="{ba.esc(article["capa"]["alt"])}" loading="lazy"></div>\n'
        '      <div class="blog-card-body">\n'
        f'        <span class="blog-card-cat">{cat_label}</span>\n'
        f'        <h2>{article["titulo_h1"]}</h2>\n'
        f'        <p class="blog-card-excerpt">{excerpt}</p>\n'
        f'        <div class="blog-card-footer"><span class="blog-card-date">{date_display}</span><span class="blog-card-read">Ler artigo →</span></div>\n'
        "      </div>\n"
        "    </a>"
    )


def main():
    articles = ba.get_all_articles_sorted()

    with open(BLOG_INDEX_PATH, encoding="utf-8") as f:
        html = f.read()

    # 1) Grade de cards
    grid_start_marker = '<div class="blog-grid">'
    grid_end_marker = '  </div>\n  <p class="blog-no-results"'
    start = html.index(grid_start_marker) + len(grid_start_marker)
    end = html.index(grid_end_marker, start)

    cards_html = "\n\n    <!-- Gerado automaticamente por scripts/build_blog_index.py a partir de content/*.json -->\n"
    cards_html += "\n\n".join(build_card_html(a) for a in articles)
    cards_html += "\n\n"

    html = html[:start] + cards_html + html[end:]

    # 2) Contadores do filtro (recalculados a partir dos artigos reais)
    counts = {}
    for a in articles:
        cat_slug = CAT_SLUG_MAP.get(a["categoria"], a["categoria"])
        counts[cat_slug] = counts.get(cat_slug, 0) + 1
    total = len(articles)

    def replace_count(html, cat_arg, count):
        pattern = re.compile(
            rf"(filterBlog\('{cat_arg}',this\)\">[^<]*<span class=\"blog-filter-count\">)\d+(</span>)"
        )
        return pattern.sub(lambda m: f"{m.group(1)}{count}{m.group(2)}", html)

    html = replace_count(html, "all", total)
    for cat_slug in ("saude", "ortodontia", "tratamentos", "gestantes", "curiosidades"):
        html = replace_count(html, cat_slug, counts.get(cat_slug, 0))

    with open(BLOG_INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"OK - {total} cards gerados, ordenados por data (mais recente primeiro)")
    for cat_slug, count in sorted(counts.items()):
        print(f"  {cat_slug}: {count}")


if __name__ == "__main__":
    main()
