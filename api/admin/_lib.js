// Utilitarios do admin do glossario (Vercel Functions, Node, sem dependencias).
// Variaveis de ambiente (painel da Vercel):
//   ADMIN_PASSWORD  senha de acesso ao /admin/
//   ADMIN_SECRET    texto longo e aleatorio, usado para assinar o cookie de sessao
//   GITHUB_TOKEN    token (fine-grained) com Contents: read/write e Actions: read neste repositorio
//   GITHUB_REPO     opcional, padrao StelleOdontologia/Site-Novo-Stelle
const crypto = require("crypto");

const REPO = process.env.GITHUB_REPO || "StelleOdontologia/Site-Novo-Stelle";
const API = process.env.GITHUB_API || "https://api.github.com";
const BRANCH = "main";
const ARQ_TERMOS = "content/glossario/termos.json";
const ARQ_AUTORES = "content/autores.json";
const COOKIE = "stelle_admin";
const DURACAO_S = 12 * 3600;
const META = [100, 200];

// ───────── resposta / corpo ─────────
function json(res, codigo, obj, extra) {
  res.statusCode = codigo;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  if (extra) for (const [k, v] of Object.entries(extra)) res.setHeader(k, v);
  res.end(JSON.stringify(obj));
}

async function corpo(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string" && req.body) return JSON.parse(req.body);
  const partes = [];
  let tamanho = 0;
  for await (const p of req) {
    tamanho += p.length;
    if (tamanho > 200000) throw new Error("Corpo grande demais.");
    partes.push(p);
  }
  const txt = Buffer.concat(partes).toString("utf8");
  return txt ? JSON.parse(txt) : {};
}

// ───────── sessao ─────────
function assinar(valor) {
  return crypto.createHmac("sha256", process.env.ADMIN_SECRET || "").update(valor).digest("hex");
}

function criarCookie() {
  const exp = Math.floor(Date.now() / 1000) + DURACAO_S;
  const token = `${exp}.${assinar(String(exp))}`;
  const seguro = process.env.VERCEL ? "; Secure" : "";
  return `${COOKIE}=${token}; HttpOnly${seguro}; SameSite=Strict; Path=/; Max-Age=${DURACAO_S}`;
}

function limparCookie() {
  const seguro = process.env.VERCEL ? "; Secure" : "";
  return `${COOKIE}=; HttpOnly${seguro}; SameSite=Strict; Path=/; Max-Age=0`;
}

function iguais(a, b) {
  const x = crypto.createHash("sha256").update(String(a)).digest();
  const y = crypto.createHash("sha256").update(String(b)).digest();
  return crypto.timingSafeEqual(x, y);
}

function logado(req) {
  if (!process.env.ADMIN_SECRET || process.env.ADMIN_SECRET.length < 16) return false;
  const m = /(?:^|;\s*)stelle_admin=([^;]+)/.exec(req.headers.cookie || "");
  if (!m) return false;
  const [exp, sig] = m[1].split(".");
  if (!exp || !sig || Number(exp) < Date.now() / 1000) return false;
  return iguais(sig, assinar(exp));
}

function configurado() {
  return !!(process.env.ADMIN_PASSWORD && process.env.ADMIN_SECRET && process.env.GITHUB_TOKEN);
}

// Texto do problema de configuração, ou null se está tudo certo.
function problemaConfig() {
  if (!process.env.ADMIN_PASSWORD || !process.env.ADMIN_SECRET || !process.env.GITHUB_TOKEN) {
    return "O admin ainda não foi configurado na Vercel (ADMIN_PASSWORD, ADMIN_SECRET e GITHUB_TOKEN).";
  }
  if (process.env.ADMIN_SECRET.length < 16) {
    return "O ADMIN_SECRET na Vercel precisa ter pelo menos 16 caracteres. Aumente o texto e faça um novo deploy.";
  }
  return null;
}

// ───────── GitHub ─────────
async function gh(metodo, caminho, dados) {
  const r = await fetch(`${API}/repos/${REPO}/${caminho}`, {
    method: metodo,
    headers: {
      Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "stelle-admin-glossario",
      ...(dados ? { "Content-Type": "application/json" } : {}),
    },
    body: dados ? JSON.stringify(dados) : undefined,
  });
  let corpoResp = null;
  try { corpoResp = await r.json(); } catch (_) { /* sem corpo */ }
  return { status: r.status, dados: corpoResp };
}

async function lerArquivo(caminho) {
  const r = await gh("GET", `contents/${caminho}?ref=${BRANCH}`);
  if (r.status !== 200) throw new Error(`Não consegui ler ${caminho} no GitHub (HTTP ${r.status}).`);
  return { texto: Buffer.from(r.dados.content, "base64").toString("utf8"), sha: r.dados.sha };
}

async function gravarArquivo(caminho, texto, sha, mensagem) {
  const r = await gh("PUT", `contents/${caminho}`, {
    message: mensagem, content: Buffer.from(texto, "utf8").toString("base64"), sha, branch: BRANCH,
    committer: { name: "Admin Glossario", email: "admin-glossario@users.noreply.github.com" },
  });
  if (r.status === 409 || r.status === 422) throw new Error("O arquivo mudou enquanto você editava. Recarregue a página e tente de novo.");
  if (r.status !== 200 && r.status !== 201) throw new Error(`O GitHub recusou a gravação (HTTP ${r.status}). Confira o token.`);
}

async function paginaExiste(link) {
  const p = String(link).replace(/^\/+|\/+$/g, "");
  if (/[^a-zA-Z0-9\-_/]/.test(p) || p.includes("..")) return false;
  const r = await gh("GET", `contents/${p ? p + "/" : ""}index.html?ref=${BRANCH}`);
  return r.status === 200;
}

// ───────── dados ─────────
async function carregar() {
  const [t, a] = await Promise.all([lerArquivo(ARQ_TERMOS), lerArquivo(ARQ_AUTORES)]);
  const autores = JSON.parse(a.texto);
  const revisores = {};
  for (const [k, v] of Object.entries(autores)) revisores[k] = `${v.nome} (${v.cro})`;
  return { doc: JSON.parse(t.texto), sha: t.sha, revisores };
}

function publico(estado) {
  return { termos: estado.doc.termos, revisores: estado.revisores, meta: META };
}

function serializar(doc) {
  return JSON.stringify(doc, null, 2) + "\n";
}

function slugify(txt) {
  return String(txt).normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/\(.*?\)/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

// Só marcações simples de texto; qualquer outra coisa é recusada (o texto vai direto para a página pública).
function htmlSeguro(txt, campo) {
  const tags = String(txt).match(/<[^>]*>/g) || [];
  for (const t of tags) {
    if (/^<\/?(strong|em|b|i|br)\s*\/?>$/i.test(t)) continue;
    if (/^<a\s+href="(\/[^"\s<>]*|https:\/\/[^"\s<>]+)"(\s+target="_blank")?(\s+rel="[a-z ]+")?\s*>$/i.test(t)) continue;
    if (/^<\/a>$/i.test(t)) continue;
    throw new Error(`Em "${campo}": só são permitidos <strong>, <em> e links. Trecho recusado: ${t.slice(0, 40)}`);
  }
  if (/[<>]/.test(String(txt).replace(/<[^>]*>/g, ""))) throw new Error(`Em "${campo}": há um sinal < ou > solto.`);
}

function contarPalavras(t) {
  return [t.definicao, ...t.texto].join(" ").replace(/<[^>]+>/g, "").split(/\s+/).filter(Boolean).length;
}

const mesmoConteudo = (a, b) => ["termo", "definicao", "texto", "links", "relacionados", "meta_description"]
  .every((k) => JSON.stringify(a[k] ?? null) === JSON.stringify(b[k] ?? null));

// ───────── ações ─────────
async function executar(acao, p, estado) {
  const { doc, revisores } = estado;
  const achar = (slug) => doc.termos.find((x) => x.slug === slug);
  let mensagem;
  let aviso = null;

  if (acao === "salvar") {
    const t = achar(p.slug);
    if (!t) throw new Error("Termo não encontrado.");
    const antes = JSON.parse(JSON.stringify(t));
    const novo = {
      termo: String(p.termo || "").trim(),
      definicao: String(p.definicao || "").trim(),
      texto: (p.texto || []).map((x) => String(x).trim()).filter(Boolean),
      links: (p.links || []).map(([a, b]) => [String(a).trim(), String(b).trim()]).filter(([a, b]) => a && b),
      relacionados: (p.relacionados || []).map((x) => String(x).trim()).filter(Boolean),
    };
    const meta = String(p.meta_description || "").trim();
    if (!novo.termo || !novo.definicao || !novo.texto.length) throw new Error("Preencha nome, definição e pelo menos um parágrafo.");
    if (novo.termo.length > 120 || meta.length > 300 || novo.texto.length > 12) throw new Error("Algum campo ficou grande demais.");
    htmlSeguro(novo.definicao, "Definição");
    novo.texto.forEach((x, i) => htmlSeguro(x, `Parágrafo ${i + 1}`));
    if (/[<>"]/.test(novo.termo + meta)) throw new Error("Nome e descrição não podem ter < > ou aspas.");
    for (const r of novo.relacionados) if (!achar(r) || r === t.slug) throw new Error(`Termo relacionado inexistente: ${r}`);
    for (const [c, n] of novo.links) {
      htmlSeguro(n, "Texto do link");
      if (!(await paginaExiste(c))) throw new Error(`Esse endereço não existe no site: ${c}`);
    }
    Object.assign(t, novo);
    if (meta) t.meta_description = meta; else delete t.meta_description;
    if (t.revisado && !mesmoConteudo(antes, t)) {
      t.revisado = false; delete t.revisado_por; aviso = "A aprovação foi retirada porque o texto mudou.";
    }
    mensagem = `Glossario (admin): edita "${t.termo}"`;
  } else if (acao === "aprovar") {
    const t = achar(p.slug);
    if (!t) throw new Error("Termo não encontrado.");
    if (p.aprovar) {
      if (!revisores[p.revisor]) throw new Error("Escolha quem revisou.");
      const n = contarPalavras(t);
      if (n < META[0] || n > META[1]) throw new Error(`O texto tem ${n} palavras; para aprovar precisa ficar entre ${META[0]} e ${META[1]}.`);
      const hoje = new Date(Date.now() - 3 * 3600 * 1000).toISOString().slice(0, 10);
      t.revisado = true; t.revisado_por = p.revisor;
      if (!t.publicado_em) t.publicado_em = hoje;
      t.atualizado_em = hoje;
      mensagem = `Glossario (admin): aprova "${t.termo}"`;
    } else {
      t.revisado = false; delete t.revisado_por;
      mensagem = `Glossario (admin): tira aprovação de "${t.termo}"`;
    }
  } else if (acao === "novo") {
    const nome = String(p.termo || "").trim();
    const slug = slugify(nome);
    if (!slug || /[<>"]/.test(nome)) throw new Error("Nome inválido.");
    if (achar(slug)) throw new Error("Já existe um termo com esse endereço.");
    doc.termos.push({ slug, termo: nome, definicao: `<strong>${nome}</strong> é ...`, texto: ["Escreva aqui."], relacionados: [], links: [] });
    mensagem = `Glossario (admin): cria rascunho "${nome}"`;
    p.slug = slug;
  } else if (acao === "excluir") {
    const t = achar(p.slug);
    if (!t) throw new Error("Termo não encontrado.");
    if (t.revisado) throw new Error("Termo aprovado: tire a aprovação antes de excluir.");
    doc.termos = doc.termos.filter((x) => x.slug !== p.slug);
    doc.termos.forEach((x) => { x.relacionados = (x.relacionados || []).filter((r) => r !== p.slug); });
    mensagem = `Glossario (admin): exclui rascunho "${t.termo}"`;
  } else {
    throw new Error("Ação desconhecida.");
  }
  return { mensagem, aviso, slug: p.slug };
}

module.exports = {
  json, corpo, logado, criarCookie, limparCookie, iguais, configurado, problemaConfig, gh, carregar, publico,
  serializar, gravarArquivo, executar, ARQ_TERMOS,
};
