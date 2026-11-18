const L = require("./_lib");

// Situação da última geração automática das páginas (workflow "Glossario" no GitHub Actions).
module.exports = async (req, res) => {
  if (req.method !== "GET") return L.json(res, 405, { erro: "Método não permitido." });
  if (!L.logado(req)) return L.json(res, 401, { erro: "Sessão expirada." });
  try {
    const r = await L.gh("GET", "actions/workflows/glossario.yml/runs?per_page=1&branch=main");
    if (r.status !== 200) return L.json(res, 200, { situacao: "desconhecida" });
    const run = (r.dados.workflow_runs || [])[0];
    if (!run) return L.json(res, 200, { situacao: "nenhuma" });
    let situacao = "publicando";
    if (run.status === "completed") situacao = run.conclusion === "success" ? "publicado" : "falhou";
    return L.json(res, 200, { situacao, quando: run.updated_at, link: run.html_url });
  } catch (_) {
    return L.json(res, 200, { situacao: "desconhecida" });
  }
};
