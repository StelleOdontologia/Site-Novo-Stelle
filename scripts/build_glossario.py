# -*- coding: utf-8 -*-
"""
Gera o glossario (/glossario/ e /glossario/<termo>/) a partir de
content/glossario/termos.json.

Uso:
    python3 scripts/build_glossario.py               # so termos revisados (producao)
    python3 scripts/build_glossario.py --rascunhos   # inclui rascunhos (noindex) para conferir o visual

Regras:
- Fonte da verdade = content/glossario/termos.json. Nunca edite os index.html gerados.
- Termo so entra no site publico (indice, sitemap, indexavel) com
  "revisado": true e "revisado_por" preenchido (chave de content/autores.json).
- Rascunhos gerados com --rascunhos saem com noindex e ficam fora do indice
  e do sitemap. Antes de subir o site, rode o comando SEM a flag.
- Cabecalho, rodape e CSS vem de templates/artigo.html, entao qualquer
  mudanca de menu feita la se propaga para o glossario no proximo build.
"""
import json
import os
import re
import shutil
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "content", "glossario", "termos.json")
TEMPLATE_PATH = os.path.join(ROOT, "templates", "artigo.html")
AUTORES_PATH = os.path.join(ROOT, "content", "autores.json")
OUT_DIR = os.path.join(ROOT, "glossario")
BASE_URL = "https://stelleodontologia.com.br"
MARCADOR = "STELLE-GLOSSARIO-GERADO"  # permite apagar so o que este script criou
PALAVRAS_MIN, PALAVRAS_MAX = 100, 200

ROBOTS_INDEX = "follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large"
ROBOTS_NOINDEX = "noindex, nofollow"

CSS_EXTRA = """
  /* ── GLOSSARIO ───────────────────────────── */
  .gl-wrap { max-width: 780px; margin: 0 auto; padding: 24px 20px 56px; }
  .gl-wrap h1 { font-size: clamp(1.7rem, 4vw, 2.3rem); line-height: 1.2; margin: 8px 0 18px; }
  .gl-lead { font-size: 1.12rem; line-height: 1.7; color: #1a2340; border-left: 4px solid #01aeb7; padding: 4px 0 4px 16px; margin: 0 0 20px; }
  .gl-wrap p { font-size: 1.04rem; line-height: 1.75; margin: 0 0 16px; }
  .gl-box { background: #f3fafb; border: 1px solid #d3eef0; border-radius: 12px; padding: 18px 20px; margin: 28px 0; }
  .gl-box h2 { font-size: 1.05rem; margin: 0 0 10px; }
  .gl-box ul { margin: 0; padding-left: 20px; }
  .gl-box li { margin-bottom: 6px; line-height: 1.5; }
  .gl-box a { color: #0a6f76; font-weight: 600; }
  .gl-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; list-style: none; }
  .gl-chips a { display: inline-block; padding: 7px 14px; border-radius: 999px; background: #fff; border: 1px solid #c9d3e0; color: #1a2340; text-decoration: none; font-size: 14px; font-weight: 500; }
  .gl-chips a:hover { border-color: #01aeb7; color: #0a6f76; }
  .gl-revisao { font-size: .9rem; color: #5a6475; margin: 24px 0 0; }
  .gl-aviso { font-size: .85rem; color: #5a6475; border-top: 1px solid #e3e7ee; padding-top: 14px; margin-top: 28px; }
  .gl-cta { display: inline-block; background: #01aeb7; color: #fff !important; padding: 12px 24px; border-radius: 50px; font-weight: 700; text-decoration: none; margin-top: 6px; }
  .gl-cta:hover { background: #019aa3; }
  .gl-rascunho { background: #fff4d6; border: 1px solid #f0c24b; color: #6b4e00; padding: 10px 14px; border-radius: 8px; margin-bottom: 18px; font-size: .92rem; }
  .gl-search { width: 100%; padding: 14px 18px; font-size: 1rem; border: 2px solid #c9d3e0; border-radius: 10px; font-family: inherit; box-sizing: border-box; }
  .gl-search:focus { outline: none; border-color: #01aeb7; box-shadow: 0 0 0 4px rgba(1,174,183,.15); }
  .gl-alpha { display: flex; flex-wrap: wrap; gap: 6px; margin: 18px 0 8px; padding: 0; list-style: none; }
  .gl-alpha a, .gl-alpha span { display: inline-flex; align-items: center; justify-content: center; width: 38px; height: 38px; border-radius: 8px; font-weight: 700; font-size: .9rem; text-decoration: none; }
  .gl-alpha a { background: #eef2f7; color: #1a2340; border: 1px solid #d5dce6; }
  .gl-alpha a:hover { background: #01aeb7; color: #fff; border-color: #01aeb7; }
  .gl-alpha span { color: #b6bfcc; border: 1px solid #eef0f4; }
  .gl-letra { margin-top: 30px; scroll-margin-top: 90px; }
  .gl-letra h2 { font-size: 2rem; color: #01aeb7; border-bottom: 2px solid #e3e7ee; padding-bottom: 6px; margin: 0 0 12px; }
  .gl-letra h2 small { font-size: .85rem; color: #7b8494; font-weight: 400; margin-left: 8px; }
  .gl-lista { list-style: none; margin: 0; padding: 0; }
  .gl-lista li { border-bottom: 1px solid #eef0f4; }
  .gl-lista a { display: block; padding: 10px 2px; color: #1a2340; text-decoration: none; font-weight: 600; }
  .gl-lista a span { display: block; font-weight: 400; font-size: .9rem; color: #5a6475; margin-top: 2px; }
  .gl-lista a:hover { color: #0a6f76; }
  .gl-vazio { display: none; padding: 18px 0; color: #5a6475; }
"""


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def fold(s):
    """Minuscula sem acento (para ordenar e achar a letra inicial)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


def letra_de(termo):
    for ch in fold(termo):
        if ch.isalpha():
            return ch.upper()
    return "#"


def carregar():
    with open(DATA_PATH, encoding="utf-8") as f:
        termos = json.load(f)["termos"]
    with open(AUTORES_PATH, encoding="utf-8") as f:
        autores = json.load(f)

    slugs = set()
    for t in termos:
        assert t["slug"] not in slugs, f"slug duplicado: {t['slug']}"
        slugs.add(t["slug"])
        t["_publico"] = bool(t.get("revisado")) and bool(t.get("revisado_por"))
        if t.get("revisado") and not t.get("revisado_por"):
            sys.exit(f"ERRO: '{t['slug']}' esta revisado=true mas sem revisado_por.")
        if t.get("revisado_por") and t["revisado_por"] not in autores:
            sys.exit(f"ERRO: revisado_por '{t['revisado_por']}' nao existe em autores.json ({t['slug']}).")
        for caminho, _ in t.get("links", []):
            if not os.path.isfile(os.path.join(ROOT, caminho.strip("/"), "index.html")):
                sys.exit(f"ERRO: link inexistente em '{t['slug']}': {caminho}")
    for t in termos:
        for r in t.get("relacionados", []):
            if r not in slugs:
                sys.exit(f"ERRO: relacionado '{r}' nao existe (termo {t['slug']}).")
    return termos, autores


def contar_palavras(t):
    texto = strip_tags(" ".join([t["definicao"]] + t["texto"]))
    return len(texto.split())


def template_base(rascunho_global):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        html = f.read()
    html = re.sub(
        r"<!--\s*STELLE ODONTOLOGIA — Artigo gerado.*?-->",
        f"<!-- STELLE ODONTOLOGIA — {MARCADOR} por scripts/build_glossario.py. "
        "Fonte: content/glossario/termos.json — NAO EDITE ESTE ARQUIVO DIRETAMENTE. -->",
        html, count=1, flags=re.S,
    )
    html = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="{{ROBOTS}}">', html, count=1)
    html = html.replace('<meta property="og:type" content="article">', '<meta property="og:type" content="{{OG_TYPE}}">')
    html = re.sub(r"<main>.*?</main>", "<main>\n{{MAIN_HTML}}\n</main>", html, count=1, flags=re.S)
    html = html.replace("</style>\n</head>", CSS_EXTRA + "</style>\n</head>", 1)
    html = html.replace("{{OG_IMAGE}}", f"{BASE_URL}/assets/logo.png")
    return html


def aplicar(base, valores):
    html = base
    for k, v in valores.items():
        html = html.replace("{{" + k + "}}", v)
    restante = re.search(r"\{\{[^}]*\}\}", html)
    assert not restante, f"placeholder nao substituido: {restante.group(0)}"
    return html


def breadcrumb_schema(itens):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@id": url, "name": nome}}
            for i, (nome, url) in enumerate(itens)
        ],
    }


def pagina_termo(base, t, termos_por_slug, autores, publicos):
    url = f"{BASE_URL}/glossario/{t['slug']}/"
    titulo_h1 = f"O que é {t['termo']}?"
    titulo_meta = t.get("titulo_meta") or f"{t['termo']}: o que é | Glossário Stelle Odontologia"
    descricao = t.get("meta_description") or strip_tags(t["definicao"])
    if len(descricao) > 158:
        descricao = descricao[:155].rsplit(" ", 1)[0] + "..."

    rascunho = not t["_publico"]

    grafo = [
        breadcrumb_schema([("Início", BASE_URL + "/"), ("Glossário", BASE_URL + "/glossario/"), (t["termo"], url)]),
        {
            "@type": "DefinedTerm",
            "@id": url + "#termo",
            "name": re.sub(r"\s*\(.*?\)\s*", " ", t["termo"]).strip(),
            "description": strip_tags(" ".join([t["definicao"]] + t["texto"])),
            "url": url,
            "inDefinedTermSet": {"@id": BASE_URL + "/glossario/#glossario"},
        },
    ]
    if t.get("revisado_por"):
        a = autores[t["revisado_por"]]
        grafo.append({
            "@type": "WebPage", "@id": url, "url": url, "name": titulo_meta,
            "reviewedBy": {"@type": "Person", "name": a["nome"], "url": a["url"], "jobTitle": a["cargo"]},
            "isPartOf": {"@id": BASE_URL + "/glossario/#glossario"},
        })
    schema = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False)

    corpo = []
    if rascunho:
        corpo.append('<div class="gl-rascunho"><strong>RASCUNHO</strong> — texto ainda não revisado. Esta página está com noindex e não aparece no índice nem no sitemap.</div>')
    corpo.append(f'<h1>{esc(titulo_h1)}</h1>')
    corpo.append(f'<p class="gl-lead">{t["definicao"]}</p>')
    corpo += [f"<p>{p}</p>" for p in t["texto"]]

    if t.get("links"):
        itens = "".join(f'<li><a href="{c}">{esc(n)}</a></li>' for c, n in t["links"])
        corpo.append(f'<div class="gl-box"><h2>Quer se aprofundar?</h2><ul>{itens}</ul></div>')

    rels = [termos_por_slug[r] for r in t.get("relacionados", []) if r in publicos or rascunho]
    if rels:
        chips = "".join(f'<li><a href="/glossario/{r["slug"]}/">{esc(r["termo"])}</a></li>' for r in rels)
        corpo.append(f'<h2 style="font-size:1.1rem;margin:28px 0 12px;">Termos relacionados</h2><ul class="gl-chips">{chips}</ul>')

    if t.get("revisado_por"):
        a = autores[t["revisado_por"]]
        corpo.append(f'<p class="gl-revisao">Conteúdo revisado por <strong>{esc(a["nome"])}</strong> ({esc(a["cro"])}).</p>')
    corpo.append(
        '<p class="gl-aviso">Este conteúdo é informativo e não substitui a avaliação de um dentista. '
        'Em caso de dor, sangramento ou qualquer dúvida sobre a sua saúde bucal, agende uma consulta.</p>'
    )
    corpo.append('<a class="gl-cta" href="https://wa.me/5521976939004" target="_blank" rel="noopener">📱 Agendar avaliação</a>')
    corpo.append('<p style="margin-top:28px;"><a href="/glossario/">← Voltar ao glossário</a></p>')

    main = (
        '<div class="article-breadcrumb"><a href="/">Início</a> &gt; <a href="/glossario/">Glossário</a> &gt; '
        f'{esc(t["termo"])}</div>\n<article class="gl-wrap">\n' + "\n".join(corpo) + "\n</article>"
    )
    return aplicar(base, {
        "TITLE_META": esc(titulo_meta), "META_DESCRIPTION": esc(descricao), "CANONICAL_URL": url,
        "SCHEMA_JSON": schema, "MAIN_HTML": main,
        "ROBOTS": ROBOTS_NOINDEX if rascunho else ROBOTS_INDEX, "OG_TYPE": "article",
    })


def pagina_indice(base, termos_listados, rascunho_global):
    url = BASE_URL + "/glossario/"
    por_letra = {}
    for t in sorted(termos_listados, key=lambda x: fold(x["termo"])):
        por_letra.setdefault(letra_de(t["termo"]), []).append(t)

    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    nav = "".join(
        f'<li><a href="#letra-{L}">{L}</a></li>' if L in por_letra else f"<li><span>{L}</span></li>"
        for L in alfabeto
    )
    blocos = []
    for L in sorted(por_letra):
        n = len(por_letra[L])
        itens = "".join(
            f'<li data-busca="{esc(fold(t["termo"] + " " + strip_tags(t["definicao"])))}">'
            f'<a href="/glossario/{t["slug"]}/">{esc(t["termo"])}<span>{esc(strip_tags(t["definicao"]))}</span></a></li>'
            for t in por_letra[L]
        )
        blocos.append(
            f'<section class="gl-letra" id="letra-{L}"><h2>{L}<small>{n} termo{"s" if n != 1 else ""}</small></h2>'
            f'<ul class="gl-lista">{itens}</ul></section>'
        )

    aviso = ""
    if rascunho_global:
        aviso = '<div class="gl-rascunho"><strong>MODO RASCUNHO</strong> — este índice inclui termos não revisados. Rode o build sem --rascunhos antes de publicar.</div>'

    schema = json.dumps({"@context": "https://schema.org", "@graph": [
        breadcrumb_schema([("Início", BASE_URL + "/"), ("Glossário", url)]),
        {"@type": "CollectionPage", "@id": url, "url": url, "name": "Glossário de Odontologia"},
        {"@type": "DefinedTermSet", "@id": url + "#glossario", "name": "Glossário de Odontologia — Stelle Odontologia", "url": url,
         "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t["termo"], "url": f"{BASE_URL}/glossario/{t['slug']}/"} for t in termos_listados]},
    ]}, ensure_ascii=False)

    js = """<script>
(function(){
  var q=document.getElementById('gl-busca'), vazio=document.getElementById('gl-vazio');
  function fold(s){return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');}
  q.addEventListener('input',function(){
    var v=fold(q.value.trim()), achou=0;
    document.querySelectorAll('.gl-lista li').forEach(function(li){
      var ok=!v||li.getAttribute('data-busca').indexOf(v)!==-1; li.style.display=ok?'':'none'; if(ok)achou++;
    });
    document.querySelectorAll('.gl-letra').forEach(function(s){
      s.style.display=s.querySelector('li:not([style*="none"])')?'':'none';
    });
    vazio.style.display=achou?'none':'block';
  });
})();
</script>"""

    main = (
        '<div class="article-breadcrumb"><a href="/">Início</a> &gt; Glossário</div>\n<div class="gl-wrap">\n'
        f'{aviso}<h1>Glossário de Odontologia</h1>\n'
        '<p class="gl-lead">Os principais termos da saúde bucal explicados de forma simples, para você entender seu tratamento e conversar melhor com o dentista.</p>\n'
        '<input id="gl-busca" class="gl-search" type="search" placeholder="Buscar um termo (ex.: bruxismo)" aria-label="Buscar termo no glossário">\n'
        f'<ul class="gl-alpha" aria-label="Navegar por letra">{nav}</ul>\n'
        '<p id="gl-vazio" class="gl-vazio">Nenhum termo encontrado. Tente outra palavra.</p>\n'
        + "\n".join(blocos) + "\n</div>\n" + js
    )
    return aplicar(base, {
        "TITLE_META": "Glossário de Odontologia: termos explicados | Stelle Odontologia",
        "META_DESCRIPTION": "Glossário de odontologia com os principais termos explicados de forma simples: bruxismo, gengivite, implante, alinhadores e muito mais.",
        "CANONICAL_URL": url, "SCHEMA_JSON": schema, "MAIN_HTML": main,
        "ROBOTS": ROBOTS_NOINDEX if rascunho_global else ROBOTS_INDEX, "OG_TYPE": "website",
    })


def remover_pasta(caminho, tentativas=3):
    """No Windows, o app/antivirus podem segurar o arquivo por instantes: tenta de novo e,
    se persistir, usa 'rd' do Windows (que costuma conseguir)."""
    import subprocess
    import time
    for _ in range(tentativas):
        try:
            shutil.rmtree(caminho)
            return
        except PermissionError:
            time.sleep(1)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "rd", "/s", "/q", caminho], check=False)
    if os.path.exists(caminho):
        print(f"AVISO  nao consegui apagar {caminho} (arquivo em uso). Apague a pasta a mao antes de subir o site.")


def escrever_modelo_previa(base):
    """Gera admin/modelo-previa.html: a pagina completa (menu, rodape, CSS reais) com
    marcadores [[...]] que o admin online preenche no navegador para mostrar a previa
    de um termo, inclusive texto ainda nao salvo."""
    html = base
    fixos = {
        "ROBOTS": "noindex, nofollow", "OG_TYPE": "article", "SCHEMA_JSON": "{}",
        "CANONICAL_URL": BASE_URL + "/admin/",
    }
    for k, v in fixos.items():
        html = html.replace("{{" + k + "}}", v)
    for k in ("TITLE_META", "META_DESCRIPTION", "MAIN_HTML"):
        html = html.replace("{{" + k + "}}", "[[" + k + "]]")
    restante = re.search(r"\{\{[^}]*\}\}", html)
    assert not restante, f"placeholder nao tratado no modelo: {restante.group(0)}"
    escrever(os.path.join(ROOT, "admin", "modelo-previa.html"), html)


def escrever(caminho, html):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)


def main():
    rascunhos = "--rascunhos" in sys.argv
    termos, autores = carregar()
    por_slug = {t["slug"]: t for t in termos}
    publicos = {t["slug"] for t in termos if t["_publico"]}
    incluidos = [t for t in termos if rascunhos or t["_publico"]]

    for t in termos:
        n = contar_palavras(t)
        if not (PALAVRAS_MIN <= n <= PALAVRAS_MAX):
            print(f"AVISO  {t['slug']}: {n} palavras (meta {PALAVRAS_MIN}-{PALAVRAS_MAX})")

    base = template_base(rascunhos)
    escrever_modelo_previa(base)

    # remove paginas geradas antes que nao devem mais existir (so as criadas por este script)
    if os.path.isdir(OUT_DIR):
        manter = {t["slug"] for t in incluidos}
        for nome in os.listdir(OUT_DIR):
            p = os.path.join(OUT_DIR, nome, "index.html")
            if nome not in manter and os.path.isfile(p):
                with open(p, encoding="utf-8") as f:
                    if MARCADOR in f.read(600):
                        remover_pasta(os.path.join(OUT_DIR, nome))

    if not incluidos:
        idx = os.path.join(OUT_DIR, "index.html")
        if os.path.isfile(idx):
            os.remove(idx)
        print("Nenhum termo revisado ainda: nada publicado (glossario/ nao foi gerado).")
        return

    for t in incluidos:
        escrever(os.path.join(OUT_DIR, t["slug"], "index.html"), pagina_termo(base, t, por_slug, autores, publicos))
    escrever(os.path.join(OUT_DIR, "index.html"), pagina_indice(base, incluidos, rascunhos))

    pub, rasc = sum(1 for t in incluidos if t["_publico"]), sum(1 for t in incluidos if not t["_publico"])
    print(f"OK  glossario: {pub} publicados, {rasc} rascunhos (noindex) -> glossario/")


if __name__ == "__main__":
    main()
