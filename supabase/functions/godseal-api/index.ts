// GodSeal AI API — Supabase Edge Function
// 路由：GET /health、GET /sigils、POST /interpret、POST /creations、GET /creations/:id
import { createClient } from "jsr:@supabase/supabase-js@2";
import {
  buildSystemPrompt,
  buildUserPrompt,
  parsePlan,
  type Sigil,
  usableSigils,
  validateSequence,
} from "./engine.ts";
import { createProviders, generateWithFallback } from "./providers.ts";

const env = (k: string) => Deno.env.get(k);

const db = createClient(env("SUPABASE_URL")!, env("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});

const authClient = createClient(env("SUPABASE_URL")!, env("SUPABASE_ANON_KEY")!, {
  auth: { persistSession: false, autoRefreshToken: false },
});

async function authenticatedUser(req: Request) {
  const header = req.headers.get("authorization") ?? "";
  const match = header.match(/^Bearer\\s+(.+)$/i);
  if (!match) return null;
  const { data, error } = await authClient.auth.getUser(match[1]);
  if (error || !data.user) return null;
  return data.user;
}

const DEFAULT_ORIGINS = [
  "https://kycat2026-ui.github.io",
  "https://magicaltar.art",
  "https://www.magicaltar.art",
];
const allowedOrigins = (env("ALLOWED_ORIGINS")?.split(",").map((s) => s.trim()).filter(Boolean)) ??
  DEFAULT_ORIGINS;

function corsHeaders(origin: string | null): Record<string, string> {
  const ok = origin && (allowedOrigins.includes(origin) || origin.startsWith("http://localhost"));
  return {
    "Access-Control-Allow-Origin": ok ? origin! : allowedOrigins[0],
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, apikey, x-client-info",
    Vary: "Origin",
  };
}

// 簡易速率限制（每個 IP 每分鐘 10 次 AI 請求；單一實例內有效）
const hits = new Map<string, number[]>();
function rateLimited(ip: string, limit = 10): boolean {
  const now = Date.now();
  const arr = (hits.get(ip) ?? []).filter((t) => now - t < 60_000);
  arr.push(now);
  hits.set(ip, arr);
  return arr.length > limit;
}

async function loadSigils(): Promise<Sigil[]> {
  const { data, error } = await db
    .from("sigils")
    .select("id,name,chinese_name,core,attributes,grammar_role,canonical_phrase,verification_status")
    .order("id");
  if (error) throw error;
  return (data ?? []) as Sigil[];
}

async function loadApprovedSequences(): Promise<number[][]> {
  const { data } = await db
    .from("sigil_rules")
    .select("rule_definition")
    .eq("rule_type", "approved_sequence")
    .eq("verification_status", "verified");
  return (data ?? [])
    .map((r: { rule_definition: { sigil_ids?: number[] } }) => r.rule_definition?.sigil_ids)
    .filter((x): x is number[] => Array.isArray(x));
}

Deno.serve(async (req) => {
  const cors = corsHeaders(req.headers.get("origin"));
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
    });

  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });

  const path = new URL(req.url).pathname.replace(/^.*\/godseal-api/, "") || "/";
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0].trim() ?? "unknown";

  try {
    if (req.method === "GET" && (path === "/" || path === "/health")) {
      const providers = createProviders(env);
      return json({
        service: "GodSeal AI",
        status: "online",
        ai_providers: providers.map((p) => p.name),
      });
    }

    if (req.method === "GET" && path === "/sigils") {
      const all = await loadSigils();
      return json({
        success: true,
        count: all.length,
        imported: usableSigils(all).length,
        sigils: all,
      });
    }

    if (req.method === "POST" && path === "/interpret") {
      if (rateLimited(ip)) return json({ error: "請求太頻繁，請稍後再試" }, 429);
      const body = await req.json().catch(() => ({}));
      const prompt = body?.prompt;
      if (typeof prompt !== "string" || !prompt.trim() || prompt.length > 2000) {
        return json({ error: "指令需為 1–2000 字" }, 400);
      }

      const all = await loadSigils();
      const usable = usableSigils(all);
      if (usable.length === 0) return json({ error: "尚未匯入任何符印資料" }, 503);

      const providers = createProviders(env);
      if (providers.length === 0) {
        return json({ error: "AI 金鑰尚未設定，請在 Supabase 設定 Edge Function Secrets" }, 503);
      }

      let gen;
      try {
        gen = await generateWithFallback(providers, {
          system: buildSystemPrompt(),
          prompt: buildUserPrompt(prompt.trim(), usable),
        });
      } catch (e) {
        console.error("AI providers failed:", (e as Error).message);
        return json({ error: "AI 服務暫時無法回應" }, 502);
      }

      let plan;
      try {
        plan = parsePlan(gen.response.content);
      } catch (e) {
        console.error("Plan parse failed:", (e as Error).message, gen.response.content);
        return json({ error: "AI 回傳格式不正確，請再試一次" }, 502);
      }

      const sequence = validateSequence(plan.selected_sigil_ids, all, await loadApprovedSequences());
      return json({
        success: true,
        provider: gen.response.provider,
        model: gen.response.model,
        fallback_errors: gen.errors.length,
        plan,
        sequence,
      });
    }

    if (req.method === "POST" && path === "/creations") {
      if (rateLimited(ip, 20)) return json({ error: "請求太頻繁，請稍後再試" }, 429);
      const user = await authenticatedUser(req);
      if (!user) return json({ error: "請先登入後保存作品" }, 401);
      const b = await req.json().catch(() => ({}));
      if (typeof b?.prompt !== "string" || !Array.isArray(b?.sigil_ids)) {
        return json({ error: "需要 prompt 與 sigil_ids" }, 400);
      }
      const all = await loadSigils();
      const seq = validateSequence(b.sigil_ids, all, await loadApprovedSequences());
      if (seq.status === "invalid") return json({ error: "符印序列無效", sequence: seq }, 400);

      const s = (v: unknown, n: number) => (typeof v === "string" ? v.slice(0, n) : null);
      const { data, error } = await db.from("creations").insert({
        title: s(b.title, 200),
        prompt: b.prompt.slice(0, 2000),
        sigil_sequence: seq.sigil_ids,
        interpretation: s(b.narrative, 4000),
        incantation: s(b.incantation, 2000),
        status: seq.status, // 由伺服器判定，不採用客戶端傳入值
        provider: s(b.provider, 50),
        model: s(b.model, 100),
        metadata: { translation: s(b.translation, 2000) },
        user_id: user.id,
        visibility: "private",
      }).select("id,created_at,status").single();
      if (error) throw error;
      return json({ success: true, creation: data }, 201);
    }

    const m = path.match(/^\/creations\/([0-9a-f-]{36})$/);
    if (req.method === "GET" && m) {
      const { data } = await db.from("creations")
        .select("id,title,prompt,sigil_sequence,incantation,interpretation,status,metadata,created_at,visibility,user_id")
        .eq("id", m[1]).maybeSingle();
      if (!data) return json({ error: "找不到作品" }, 404);
      if (data.visibility !== "public") {
        const user = await authenticatedUser(req);
        if (!user || user.id !== data.user_id) return json({ error: "找不到作品" }, 404);
        return json({ success: true, creation: {
          id: data.id, title: data.title, prompt: data.prompt,
          sigil_sequence: data.sigil_sequence, incantation: data.incantation,
          interpretation: data.interpretation, status: data.status,
          metadata: data.metadata, created_at: data.created_at,
        } });
      }
      // Public rows expose an explicit allowlist only.
      return json({ success: true, creation: {
        id: data.id, title: data.title, sigil_sequence: data.sigil_sequence,
        status: data.status, created_at: data.created_at,
      } });
    }

    return json({ error: "Not found" }, 404);
  } catch (e) {
    console.error("GodSeal API error:", e);
    return json({ error: "伺服器錯誤" }, 500);
  }
});
