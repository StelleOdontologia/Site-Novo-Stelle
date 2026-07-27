---
name: standardize-blog-articles
description: Padronizar header, navegação e menu de categorias de artigos do blog Stelle Odontologia
---

# Skill: Padronizar Artigos do Blog Stelle Odontologia

## Objetivo

Garantir que todo artigo do blog tenha:
1. **Header oficial** (`.stelle-header`) — logo, menu com dropdowns, CTA WhatsApp, menu mobile
2. **Menu de categorias** — filtros de categoria logo abaixo do breadcrumb
3. Sem quebrar o conteúdo do artigo, sem duplicar nada, sem referências a arquivos inexistentes

## Artigo de referência (fonte da verdade)

`mitos-e-verdades-alinhador-invisivel/index.html` — sempre copie os blocos abaixo **deste arquivo específico**, nunca de memória ou de outro artigo que ainda não foi validado.

## REGRAS DE SEGURANÇA (leia antes de tocar em qualquer arquivo)

Estas regras existem porque já causaram bugs reais em produção nesta skill:

1. **NUNCA use regex que varre um segundo arquivo inteiro sem âncora de início E fim.**
   Um bug real: `re.search(r'<script.*?</body>', outro_arquivo)` pegou o primeiro `<script>`
   do `<head>` de outro artigo e colou o arquivo inteiro (head, header, conteúdo, footer)
   dentro do artigo sendo editado. **Sempre use a ferramenta Edit com `old_string`/`new_string`
   exatos**, nunca um script Python que lê dois arquivos e concatena regiões via regex solto.

2. **Copie o HTML/CSS do header literalmente (copy-paste), não de memória.**
   Já existiram 3 headers "oficiais" diferentes espalhados pelos artigos (um deles usava
   `/assets/logo-stelle.png`, que nunca existiu — 404 confirmado). Antes de aplicar, abra
   o artigo de referência (`mitos-e-verdades-alinhador-invisivel`) e confira que a logo
   realmente carrega:
   ```bash
   curl -sI "https://stelleodontologia.com.br/assets/logo.png" | head -3
   ```
   O arquivo real do logo é **`/assets/logo.png`** — não `logo-stelle.png`.

3. **Depois de editar, sempre rode a verificação de sanidade abaixo antes de commitar.**
   Ela pega duplicações e desbalanceamentos que passam despercebidos numa leitura rápida.

4. **Sempre confirme ao vivo no navegador (produção) depois do push**, checando via
   JavaScript que os elementos esperados existem e a logo carregou (`naturalWidth > 0`).
   Vercel demora ~10-15s para propagar; se o primeiro check falhar, aguarde e recarregue
   com um query string novo (`?v=2`) para evitar cache.

## Passo a passo

### 1. Ler o header oficial do artigo de referência

Leia `mitos-e-verdades-alinhador-invisivel/index.html` e extraia (com o Read tool, não de memória):
- O bloco CSS entre `/* NAV */` e o fechamento do `@media (max-width: 768px)` do header
- O bloco HTML entre `<header class="stelle-header">` e `</header>`
- As 3 funções JS (`stelleToggleDropdown`, `stelleToggleMobile`, `stelleToggleMobileSub`)

### 2. No artigo alvo: substituir CSS do header

Localize o bloco CSS antigo do header (procure por `.site-header {` ou `.stelle-header {` —
se já for `.stelle-header`, o header já está padronizado, pule para o passo 5).

Use **Edit** (old_string = bloco CSS antigo completo, new_string = bloco oficial abaixo).

```css
/* ── HEADER OFICIAL STELLE ──────────────── */
.stelle-header { position: sticky; top: 0; left: 0; right: 0; z-index: 9999; background: #1a2340; box-shadow: 0 2px 20px rgba(0,0,0,0.25); }
.stelle-nav { max-width: 1200px; margin: 0 auto; padding: 0 40px; height: 75px; display: flex; align-items: center; justify-content: space-between; gap: 40px; }
.stelle-nav-logo { display: flex; align-items: center; flex-shrink: 0; text-decoration: none; }
.stelle-nav-logo img { height: 48px; width: auto; max-width: 180px; mix-blend-mode: screen; filter: brightness(1.1); }
.stelle-nav-links { display: flex; align-items: center; gap: 8px; list-style: none; flex: 1; justify-content: center; margin: 0; padding: 0; }
.stelle-nav-links a { color: rgba(255,255,255,0.85); text-decoration: none; font-size: 13px; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: all 0.2s; white-space: nowrap; display: flex; align-items: center; }
.stelle-nav-links a:hover { color: white; background: rgba(255,255,255,0.12); }
.stelle-nav-dropdown { position: relative; }
.stelle-nav-dropdown > a::after { content: '▼'; font-size: 8px; margin-left: 6px; }
.stelle-nav-dropdown-menu { display: none; position: absolute; top: calc(100% + 8px); left: 0; background: #0a2d4a; min-width: 220px; border-radius: 8px; padding: 8px 0; box-shadow: 0 8px 24px rgba(0,0,0,0.25); z-index: 10000; }
.stelle-nav-dropdown-menu a { display: block !important; padding: 10px 16px !important; border-radius: 0 !important; background: none !important; font-size: 13px !important; }
.stelle-nav-dropdown-menu a:hover { background: rgba(255,255,255,0.12) !important; }
.stelle-nav-dropdown.open .stelle-nav-dropdown-menu { display: block; }
.stelle-nav-cta { background: #01aeb7; color: white !important; padding: 10px 22px !important; border-radius: 50px !important; font-weight: 600 !important; display: flex !important; align-items: center; gap: 8px; flex-shrink: 0; text-decoration: none; font-size: 13px; transition: background 0.2s; white-space: nowrap; }
.stelle-nav-cta:hover { background: #019aa3 !important; }
.stelle-nav-hamburger { display: none; flex-direction: column; gap: 5px; cursor: pointer; padding: 8px; background: none; border: none; }
.stelle-nav-hamburger span { display: block; width: 24px; height: 2px; background: white; border-radius: 2px; }
.stelle-nav-mobile { display: none; flex-direction: column; background: #0a2d4a; padding: 16px 40px 20px; gap: 4px; }
.stelle-nav-mobile a { color: rgba(255,255,255,0.85); text-decoration: none; font-size: 14px; font-weight: 500; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); display: block; }
.stelle-nav-mobile.open { display: flex; }
.stelle-nav-mobile-section { border-bottom: 1px solid rgba(255,255,255,0.08); }
.stelle-nav-mobile-toggle { color: rgba(255,255,255,0.85); font-size: 14px; font-weight: 500; padding: 10px 0; display: flex; align-items: center; justify-content: space-between; cursor: pointer; background: none; border: none; width: 100%; font-family: 'Karla', sans-serif; }
.stelle-nav-mobile-toggle .arrow { transition: transform 0.2s; font-size: 10px; }
.stelle-nav-mobile-toggle.open .arrow { transform: rotate(180deg); }
.stelle-nav-mobile-sub { display: none; flex-direction: column; padding-left: 16px; padding-bottom: 6px; }
.stelle-nav-mobile-sub.open { display: flex; }
.stelle-nav-mobile-sub a { padding: 8px 0; font-size: 13px; color: rgba(255,255,255,0.72) !important; border-bottom: 1px solid rgba(255,255,255,0.05) !important; }
@media (max-width: 768px) {
  .stelle-nav-links, .stelle-nav-cta { display: none; }
  .stelle-nav-hamburger { display: flex; }
  .stelle-nav { padding: 0 20px; }
}
```

Se o artigo tinha uma media query separada referenciando a classe antiga
(ex: `.header-nav { display: none; }` dentro de outro `@media`), remova essa linha também —
ela fica órfã e não quebra nada, mas é lixo.

### 3. Adicionar CSS do menu de categorias (se ainda não existir)

Verifique com `grep -c "blog-categories-filter" arquivo.html` — se já existir, pule.

```css
/* ── MENU DE CATEGORIAS ─────────────────── */
.blog-categories-filter { background: #f5f5f5; padding: 16px 0; border-bottom: 1px solid #e0e0e0; }
.blog-categories-inner { max-width: 1200px; margin: 0 auto; padding: 0 24px; display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }
.category-btn { background: #fff; border: 1px solid #ddd; color: #3a3a3a; padding: 8px 16px; border-radius: 24px; text-decoration: none; font-size: 13px; font-weight: 500; transition: all .2s; }
.category-btn:hover { border-color: #01aeb7; color: #01aeb7; }
.category-btn.active { background: #01aeb7; color: #fff; border-color: #01aeb7; }
.category-btn .count { display: inline-block; background: rgba(0,0,0,0.1); padding: 2px 6px; border-radius: 12px; margin-left: 6px; font-size: 12px; }
.category-btn.active .count { background: rgba(255,255,255,0.3); }
```

### 4. Substituir o HTML do header

Localize `<header class="site-header">...</header>` (ou qualquer variante antiga) e
substitua pelo bloco abaixo. **Note que a logo usa `/assets/logo.png`** (não `logo-stelle.png`):

```html
<header class="stelle-header">
  <nav class="stelle-nav">
    <a href="/" class="stelle-nav-logo">
      <img src="/assets/logo.png" alt="Stelle Odontologia">
    </a>
    <ul class="stelle-nav-links">
      <li><a href="/">Início</a></li>
      <li><a href="/sobre/">A Clínica</a></li>
      <li class="stelle-nav-dropdown">
        <a href="#" onclick="stelleToggleDropdown(event,this)">Ortodontia</a>
        <div class="stelle-nav-dropdown-menu">
          <a href="/alinhadores/">Alinhadores Invisíveis</a>
          <a href="/ortodontia-miofuncional/">Ortodontia Miofuncional</a>
          <a href="/ortodontia-fixa/">Ortodontia Fixa</a>
        </div>
      </li>
      <li class="stelle-nav-dropdown">
        <a href="#" onclick="stelleToggleDropdown(event,this)">Tratamentos</a>
        <div class="stelle-nav-dropdown-menu">
          <a href="/clareamento-dental/">Clareamento Dental</a>
          <a href="/toxina-botulinica/">Toxina Botulínica</a>
          <a href="/implantes/">Implantes</a>
          <a href="/protese-dentaria/">Prótese Dentária</a>
          <a href="/endodontia/">Endodontia</a>
        </div>
      </li>
      <li><a href="/blog/">Blog</a></li>
      <li><a href="/contato/">Contato</a></li>
    </ul>
    <a href="https://wa.me/5521976939004" class="stelle-nav-cta" target="_blank" rel="noopener">
      📱 Agendar Consulta
    </a>
    <button class="stelle-nav-hamburger" onclick="stelleToggleMobile()" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </nav>
  <div class="stelle-nav-mobile" id="stelleMobileNav">
    <a href="/">Início</a>
    <a href="/sobre/">A Clínica</a>
    <div class="stelle-nav-mobile-section">
      <button class="stelle-nav-mobile-toggle" onclick="stelleToggleMobileSub(this)">Ortodontia <span class="arrow">▼</span></button>
      <div class="stelle-nav-mobile-sub">
        <a href="/alinhadores/">Alinhadores Invisíveis</a>
        <a href="/ortodontia-miofuncional/">Ortodontia Miofuncional</a>
        <a href="/ortodontia-fixa/">Ortodontia Fixa</a>
      </div>
    </div>
    <div class="stelle-nav-mobile-section">
      <button class="stelle-nav-mobile-toggle" onclick="stelleToggleMobileSub(this)">Tratamentos <span class="arrow">▼</span></button>
      <div class="stelle-nav-mobile-sub">
        <a href="/clareamento-dental/">Clareamento Dental</a>
        <a href="/toxina-botulinica/">Toxina Botulínica</a>
        <a href="/implantes/">Implantes</a>
        <a href="/protese-dentaria/">Prótese Dentária</a>
        <a href="/endodontia/">Endodontia</a>
      </div>
    </div>
    <a href="/blog/">Blog</a>
    <a href="/contato/">Contato</a>
    <a href="https://wa.me/5521976939004" target="_blank" rel="noopener">📱 Agendar Consulta</a>
  </div>
</header>
```

### 5. Inserir o menu de categorias após o breadcrumb

Ache o `<nav class="breadcrumb">...</nav>` (ou equivalente) do artigo e insira logo depois,
marcando a categoria do artigo atual com `class="category-btn active"`:

```html
<!-- MENU DE CATEGORIAS -->
<div class="blog-categories-filter">
  <div class="blog-categories-inner">
    <a href="/blog/" class="category-btn">Todos <span class="count">46</span></a>
    <a href="/blog/?cat=saude-bucal" class="category-btn">Saúde Bucal <span class="count">20</span></a>
    <a href="/blog/?cat=ortodontia" class="category-btn active">Ortodontia <span class="count">11</span></a>
    <a href="/blog/?cat=tratamentos" class="category-btn">Tratamentos <span class="count">9</span></a>
    <a href="/blog/?cat=gestantes" class="category-btn">Gestantes <span class="count">4</span></a>
    <a href="/blog/?cat=curiosidades" class="category-btn">Curiosidades <span class="count">2</span></a>
  </div>
</div>
```

> Nota: os links `/blog/?cat=X` ainda não filtram nada de verdade (a página `/blog/` não lê
> query string). Isso é um débito conhecido — ver seção "Pendências" abaixo.

### 6. Adicionar o JS de toggle antes do `</body>` (se ainda não existir)

Verifique com `grep -c "function stelleToggleDropdown" arquivo.html` — se já existir, pule.

```html
<script>
function stelleToggleDropdown(e, el) {
  e.preventDefault();
  const li = el.parentElement;
  document.querySelectorAll('.stelle-nav-dropdown.open').forEach(d => { if (d !== li) d.classList.remove('open'); });
  li.classList.toggle('open');
}
document.addEventListener('click', function(e) {
  if (!e.target.closest('.stelle-nav-dropdown')) {
    document.querySelectorAll('.stelle-nav-dropdown.open').forEach(d => d.classList.remove('open'));
  }
});
function stelleToggleMobile() {
  document.getElementById('stelleMobileNav').classList.toggle('open');
}
function stelleToggleMobileSub(btn) {
  btn.classList.toggle('open');
  btn.nextElementSibling.classList.toggle('open');
}
</script>
```

### 7. Verificação de sanidade (SEMPRE antes de commitar)

```bash
FILE="caminho/do/artigo/index.html"
echo "<html>: $(grep -c '<html' "$FILE")"          # deve ser 1
echo "</html>: $(grep -c '</html>' "$FILE")"        # deve ser 1
echo "<body: $(grep -c '<body' "$FILE")"            # deve ser 1
echo "</body>: $(grep -c '</body>' "$FILE")"        # deve ser 1
echo "stelle-header: $(grep -c 'class=\"stelle-header\"' "$FILE")"   # deve ser 1
echo "logo-stelle (bug conhecido): $(grep -c 'logo-stelle' "$FILE")" # deve ser 0
python3 -c "
import re
c = open(r'$FILE', encoding='utf-8').read()
print('div aberturas:', len(re.findall(r'<div', c)))
print('div fechamentos:', len(re.findall(r'</div>', c)))
"
```
Se qualquer contagem de `<html>`/`<body>`/`stelle-header` vier diferente de 1, ou os divs
não baterem, **pare e investigue antes de commitar** — é sinal de duplicação de conteúdo.

### 8. Commit, push, e verificação ao vivo

```bash
git add caminho/do/artigo/index.html
git commit -m "Blog: padroniza header do artigo [nome]"
git push origin main
```

Depois do push, aguarde ~10-15s e confirme via navegador (JS no console ou javascript_tool):

```js
const img = document.querySelector('.stelle-nav-logo img');
JSON.stringify({
  headerOfficial: !!document.querySelector('.stelle-header'),
  logoLoaded: img?.complete && img?.naturalWidth > 0,
  dropdownCount: document.querySelectorAll('.stelle-nav-dropdown').length,
  categoriesMenu: !!document.querySelector('.blog-categories-filter'),
  activeCategory: document.querySelector('.category-btn.active')?.textContent.trim()
});
```

Todos os campos devem vir preenchidos/`true`. Se `logoLoaded` vier `false`, o cache do
Vercel ainda não propagou — recarregue com `?v=2` ou aguarde mais.

## Status dos artigos

✅ `alinhadores-invisiveis-guia-completo-2026` — padronizado e verificado (commit `abdb33f`)
✅ `comer-e-beber-com-alinhador-invisivel` — padronizado e verificado (commits `002c595`, `3ac9b95`)
✅ `mitos-e-verdades-alinhador-invisivel` — é o artigo de referência (logo corrigida no commit `a4e06ea`)

### Pendentes

- [ ] `alinhadores-invisiveis-no-ambiente-de-trabalho`
- [ ] Demais artigos do blog (levantar lista completa antes de começar)

## Débitos técnicos conhecidos (não resolver sem alinhar com o usuário)

- Os links do menu de categorias (`/blog/?cat=ortodontia` etc.) não filtram nada de fato —
  a página `/blog/` não lê query string ainda. Isso precisa de lógica em `/blog/index.html`
  (JS que lê `?cat=` e filtra os cards) antes de ser um filtro funcional de verdade.
- Os contadores de categoria (46, 20, 11, 9, 4, 2) são fixos/hardcoded no HTML — não
  refletem a contagem real dinamicamente. Se novos artigos forem adicionados, os números
  ficam desatualizados até serem revisados manualmente.
