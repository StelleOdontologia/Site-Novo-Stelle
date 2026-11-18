const L = require("./_lib");

module.exports = async (req, res) => {
  if (req.method !== "POST") return L.json(res, 405, { erro: "Método não permitido." });
  if (req.headers["x-admin"] !== "1" || !L.logado(req)) return L.json(res, 401, { erro: "Sessão expirada. Entre de novo." });
  try {
    const p = await L.corpo(req);
    const estado = await L.carregar();
    const r = await L.executar(p.acao, p, estado);
    await L.gravarArquivo(L.ARQ_TERMOS, L.serializar(estado.doc), estado.sha, r.mensagem);
    return L.json(res, 200, { ok: true, aviso: r.aviso, slug: r.slug, ...L.publico(estado) });
  } catch (e) {
    return L.json(res, 400, { erro: e.message });
  }
};
