import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const MAX_BODY_BYTES = 8_192;
const MAX_SCOPES = 32;
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function response(body: unknown, status: number, origin: string | null) {
  const configured = (Deno.env.get("VAC_ALLOWED_ORIGINS") ?? "").split(",").map((v) => v.trim()).filter(Boolean);
  const allowedOrigin = origin && (configured.length === 0 || configured.includes(origin))
    ? (configured.length === 0 ? "*" : origin) : "null";
  return Response.json(body, { status, headers: {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "Vary": "Origin",
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  }});
}

// VAC v1 scopes are JSON Pointer-like paths through JSON objects.
// Arrays are returned only when the array-valued leaf itself is explicitly granted.
function decodePointer(scope: string): string[] | null {
  if (!scope.startsWith("/") || scope === "/" || scope.length > 512) return null;
  const parts = scope.slice(1).split("/");
  const decoded: string[] = [];
  for (const part of parts) {
    if (/~(?![01])/.test(part)) return null;
    decoded.push(part.replace(/~1/g, "/").replace(/~0/g, "~"));
  }
  if (decoded.some((p) => p.length === 0 || p === "__proto__" || p === "prototype" || p === "constructor")) return null;
  return decoded;
}

function selectAuthorizedFields(content: unknown, scopes: string[]): Record<string, unknown> | null {
  if (!content || typeof content !== "object" || Array.isArray(content)) return null;
  const output: Record<string, unknown> = {};
  for (const scope of scopes) {
    const path = decodePointer(scope);
    if (!path) return null;
    let source: any = content;
    let target: any = output;
    for (let i = 0; i < path.length; i++) {
      const key = path[i];
      if (!source || typeof source !== "object" || Array.isArray(source) ||
          !Object.prototype.hasOwnProperty.call(source, key)) return null;
      if (i === path.length - 1) {
        target[key] = source[key];
      } else {
        if (!target[key]) target[key] = {};
        source = source[key];
        target = target[key];
      }
    }
  }
  return output;
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("Origin");
  if (req.method === "OPTIONS") return response({ ok: true }, 204, origin);
  if (req.method !== "POST") return response({ error: "method_not_allowed" }, 405, origin);

  const url = Deno.env.get("SUPABASE_URL");
  const anon = Deno.env.get("SUPABASE_ANON_KEY");
  const service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const authHeader = req.headers.get("Authorization");
  if (!url || !anon || !service) return response({ error: "server_configuration_error" }, 503, origin);
  if (!authHeader || !/^Bearer\s+\S+$/i.test(authHeader)) return response({ error: "unauthorized" }, 401, origin);

  const declaredLength = Number(req.headers.get("Content-Length") ?? "0");
  if (declaredLength > MAX_BODY_BYTES) return response({ error: "request_too_large" }, 413, origin);
  let input: any;
  try {
    const raw = await req.text();
    if (new TextEncoder().encode(raw).length > MAX_BODY_BYTES) return response({ error: "request_too_large" }, 413, origin);
    input = JSON.parse(raw);
  } catch {
    return response({ error: "invalid_json" }, 400, origin);
  }

  if (!input || typeof input !== "object" || Array.isArray(input) ||
      Object.keys(input).some((k) => !["resource_id", "purpose", "scopes"].includes(k))) {
    return response({ error: "invalid_request_shape" }, 400, origin);
  }
  const resourceId = input.resource_id;
  const purpose = typeof input.purpose === "string" ? input.purpose.trim() : "";
  const scopes = input.scopes;
  if (typeof resourceId !== "string" || !UUID_RE.test(resourceId) ||
      !purpose || purpose.length > 500 ||
      !Array.isArray(scopes) || scopes.length < 1 || scopes.length > MAX_SCOPES ||
      scopes.some((s: unknown) => typeof s !== "string" || !decodePointer(s)) ||
      new Set(scopes).size !== scopes.length) {
    return response({ error: "invalid_resource_purpose_or_scopes" }, 400, origin);
  }

  try {
    const userClient = createClient(url, anon, { global: { headers: { Authorization: authHeader } } });
    const { data: authData, error: authError } = await userClient.auth.getUser();
    const subject = authData.user;
    if (authError || !subject) return response({ error: "unauthorized" }, 401, origin);

    const admin = createClient(url, service, { auth: { persistSession: false, autoRefreshToken: false } });
    const { data: resource, error: resourceError } = await admin
      .from("vac_resources").select("id,owner_id,name,content")
      .eq("id", resourceId).maybeSingle();
    if (resourceError) return response({ error: "authorization_backend_unavailable" }, 503, origin);

    let grant: any = null;
    let denial = "resource_not_found";
    if (resource) {
      denial = "no_matching_active_grant";
      const { data: grants, error: grantError } = await admin.from("vac_grants")
        .select("id,owner_id,subject_user_id,scopes,purpose,expires_at,revoked_at")
        .eq("resource_id", resourceId).eq("subject_user_id", subject.id)
        .eq("owner_id", resource.owner_id).is("revoked_at", null)
        .gt("expires_at", new Date().toISOString());
      if (grantError) return response({ error: "authorization_backend_unavailable" }, 503, origin);
      grant = (grants ?? []).find((g: any) =>
        g.purpose === purpose && Array.isArray(g.scopes) &&
        scopes.every((scope: string) => g.scopes.includes(scope))) ?? null;
    }

    const filtered = grant && resource ? selectAuthorizedFields(resource.content, scopes) : null;
    const allowed = Boolean(grant && resource && filtered !== null);
    const reason = allowed ? "active_grant_and_field_scope_match"
      : grant && resource ? "authorized_field_not_found_or_invalid_resource_shape" : denial;

    const { error: logError } = await admin.from("vac_access_log").insert({
      grant_id: grant?.id ?? null,
      resource_id: resource?.id ?? null,
      owner_id: resource?.owner_id ?? subject.id,
      subject_user_id: subject.id,
      purpose,
      requested_scopes: scopes,
      outcome: allowed ? "allowed" : "denied",
      reason,
    });
    if (logError) return response({ error: "audit_log_write_failed" }, 503, origin);
    if (!allowed) return response({ error: "access_denied", reason }, 403, origin);

    return response({
      resource: { id: resource.id, name: resource.name, content: filtered },
      authorization: { grant_id: grant.id, scopes, expires_at: grant.expires_at },
    }, 200, origin);
  } catch {
    return response({ error: "authorization_backend_unavailable" }, 503, origin);
  }
});
