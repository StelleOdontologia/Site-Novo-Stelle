const L = require("./_lib");

module.exports = async (req, res) => {
  if (req.method !== "GET") return L.json(res, 405, { erro: "Método não permitido." });
  if (!L.logado(req)) return L.json(res, 401, { erro: "Sessão expirada. Entre de novo." });
  try {
    return L.json(res, 200, L.publico(await L.carregar()));
  } catch (e) {
    return L.json(res, 502, { erro: e.message });
  }
};
