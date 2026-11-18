const L = require("./_lib");

module.exports = async (req, res) => {
  if (req.method === "GET") return L.json(res, 200, { logado: L.logado(req), configurado: !L.problemaConfig(), problema: L.problemaConfig() });
  if (req.method === "DELETE") return L.json(res, 200, { ok: true }, { "Set-Cookie": L.limparCookie() });
  if (req.method !== "POST") return L.json(res, 405, { erro: "Método não permitido." });
  if (req.headers["x-admin"] !== "1") return L.json(res, 403, { erro: "Acesso negado." });
  const problema = L.problemaConfig();
  if (problema) return L.json(res, 503, { erro: problema });
  try {
    const { senha } = await L.corpo(req);
    if (typeof senha === "string" && L.iguais(senha, process.env.ADMIN_PASSWORD)) {
      return L.json(res, 200, { ok: true }, { "Set-Cookie": L.criarCookie() });
    }
  } catch (_) { /* cai no erro abaixo */ }
  await new Promise((r) => setTimeout(r, 1200)); // dificulta tentativas em sequência
  return L.json(res, 401, { erro: "Senha incorreta." });
};
