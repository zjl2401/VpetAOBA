/**
 * Cloudflare Worker：按设备指纹自动分配桌宠编号。
 * KV 绑定：PET_ID_KV
 *
 * key:
 *  next_id
 *  dev:{machineId} -> pet_id
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }
    if (url.pathname === "/health" || url.pathname === "/") {
      return json({ ok: true, service: "vpet-pet-id", policy: "auto_assign" });
    }
    if (request.method !== "POST") {
      return json({ error: "not_found" }, 404);
    }
    let body = {};
    try {
      body = await request.json();
    } catch (_) {
      return json({ error: "invalid_json" }, 400);
    }
    const machineId = String(body.machine_id || "").trim().toLowerCase();
    if (machineId.length < 16) {
      return json({ error: "machine_id too short" }, 400);
    }
    if (url.pathname === "/v1/register" || url.pathname === "/v1/activate") {
      const existing = await env.PET_ID_KV.get(`dev:${machineId}`);
      if (existing != null && existing !== "") {
        return json({ pet_id: Number(existing), reclaimed: true, source: "device" });
      }
      let next = Number((await env.PET_ID_KV.get("next_id")) || "0");
      if (!Number.isFinite(next) || next < 0) next = 0;
      const petId = Math.floor(next);
      await env.PET_ID_KV.put("next_id", String(petId + 1));
      await env.PET_ID_KV.put(`dev:${machineId}`, String(petId));
      return json({ pet_id: petId, reclaimed: false, source: "auto" });
    }
    return json({ error: "not_found" }, 404);
  },
};

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders() },
  });
}
