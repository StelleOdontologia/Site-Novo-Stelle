---
name: standardize-blog-articles
description: Padronizar estrutura HTML de artigos do blog com header, navegação, menu de categorias
---

# Skill: Padronizar Artigos do Blog Stelle Odontologia

## Objetivo
Garantir que todos os artigos do blog tenham a mesma estrutura visual e funcional, incluindo:
1. **Header padronizado** (logo, menu de navegação, botão agendar)
2. **Menu de categorias** (filtros: Todos, Saúde Bucal, Ortodontia, Tratamentos, Gestantes, Curiosidades)
3. **Estrutura HTML consistente**
4. **Metadados e schema.org corretos**

## Estrutura do Header (Copiar do artigo modelo)

```html
<header class="site-header">
  <div class="inner">
    <a href="/" class="site-logo">
      <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <polygon points="18,3 33,12 33,24 18,33 3,24 3,12" fill="none" stroke="#01aeb7" stroke-width="2.2"/>
        <text x="18" y="23" font-size="12" fill="#fff" text-anchor="middle" font-family="Rubik" font-weight="700">S</text>
      </svg>
      Stelle Odontologia
    </a>
    <nav class="header-nav">
      <a href="/">Início</a>
      <a href="/sobre/">Sobre a Dra. Késya</a>
      <a href="/alinhadores/">Ortodontia</a>
      <a href="/blog/">Tratamentos</a>
      <a href="https://wa.me/5521976939004?text=Gostaria%20de%20mais%20informa%C3%A7%C3%B5es%20sobre%20a%20Stelle%20Odontologia" target="_blank" class="header-cta">📱 Agendar</a>
    </nav>
  </div>
</header>
```

## Estrutura do Menu de Categorias (Depois do breadcrumb)

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

## CSS do Header (Deve estar em `<style>` no `<head>`)

```css
/* ── HEADER ─────────────────────────────── */
.site-header {
  background: #1a2340;
  padding: 14px 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}
.site-header .inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.site-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #fff;
  font-family: 'Rubik', sans-serif;
  font-weight: 600;
  font-size: 20px;
  letter-spacing: -0.3px;
}
.site-logo svg { width: 36px; height: 36px; flex-shrink: 0; }
.header-nav { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.header-nav a {
  color: rgba(255,255,255,0.75);
  text-decoration: none;
  font-size: 14px;
  transition: color .2s;
}
.header-nav a:hover { color: #fff; }
.header-cta {
  background: #25d366;
  color: #fff !important;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 13px !important;
  white-space: nowrap;
}
.header-cta:hover { background: #1fb855 !important; }

/* ── MENU DE CATEGORIAS ─────────────────── */
.blog-categories-filter {
  background: #f5f5f5;
  padding: 16px 0;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 32px;
}
.blog-categories-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
}
.category-btn {
  background: #fff;
  border: 1px solid #ddd;
  color: #3a3a3a;
  padding: 8px 16px;
  border-radius: 24px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all .2s;
}
.category-btn:hover { border-color: #01aeb7; color: #01aeb7; }
.category-btn.active { background: #01aeb7; color: #fff; border-color: #01aeb7; }
.category-btn .count {
  display: inline-block;
  background: rgba(0,0,0,0.1);
  padding: 2px 6px;
  border-radius: 12px;
  margin-left: 6px;
  font-size: 12px;
}
.category-btn.active .count { background: rgba(255,255,255,0.3); }
```

## Checklist de Padronização

Para cada artigo a padronizar:

- [ ] **Header**: Adicione o `<header class="site-header">` com logo e menu de navegação
- [ ] **CSS Header**: Verifique se o CSS do header está no `<style>` do `<head>`
- [ ] **Menu de Categorias**: Adicione após o `<breadcrumb>` e antes do `<main class="article-wrap">`
- [ ] **CSS Menu**: Verifique se o CSS do menu de categorias está no `<style>`
- [ ] **Categoria Ativa**: Marque a categoria correta do artigo com `class="active"` no botão
- [ ] **Metadados**: Verifique se `<title>`, `og:title`, `description`, `og:description` estão corretos
- [ ] **Schema.org**: Verifique se o `<script type="application/ld+json">` tem os dados corretos
- [ ] **Responsivo**: Teste em mobile (viewport 375x812) para garantir que header e menu quebram bem
- [ ] **Git**: Commit com mensagem: "Blog: padroniza estrutura do artigo [título]"

## Artigos já Padronizados

✅ alinhadores-invisiveis-guia-completo-2026 (HTML puro - estrutura completa)
✅ comer-e-beber-com-alinhador-invisivel (WordPress export - header OK, menu em andamento)

## Notas Importantes

**WordPress Templates vs HTML Puro:**
- Artigos em HTML puro (como alinhadores-2026) têm estrutura limpa e aceita bm ambas as mudanças
- Artigos exportados de WordPress (como comer-e-beber) têm estrutura complexa com divs aninhadas
  - Header: inserção via regex funcionou bem
  - Menu categorias: precisa de lógica mais robusta para encontrar ponto de inserção exato
  
**Próximas iterações:**
- Considerar converter artigos WordPress para HTML puro (mais simples de manter)
- OU refinar script de inserção do menu para lidar com estrutura WordPress

## Artigos para Padronizar

- [ ] mitos-e-verdades-alinhador-invisivel
- [ ] alinhadores-invisiveis-no-ambiente-de-trabalho
- [ ] E outros artigos do blog

## Notas

- O header é **sticky** (fica no topo durante scroll)
- O menu de categorias deve ser **dinâmico** (marcar a categoria do artigo atual como "active")
- O botão de agendar usa **WhatsApp** (wa.me)
- O SVG do logo é o mesmo em todos os artigos
