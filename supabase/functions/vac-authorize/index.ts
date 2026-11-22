import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
Deno.serve(async (req: Request) => {
 if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
 const headers = { ...cors, "Content-Type": "application/json" };
 if (req.method !== "POST") return Response.json({ error: "method_not_allowed" }, { status: 405, headers });
 const url = Deno.env.get("SUPABASE_URL"), anon = Deno.env.get("SUPABASE_ANON_KEY"), service = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
 const authHeader = req.headers.get("Authorization");
 if (!url || !anon || !service || !authHeader) return Response.json({ error: "configuration_or_auth_missing" }, { status: 401, headers });
 const userClient = createClient(url, anon, { global: { headers: { Authorization: authHeader } } });
 const { data: authData, error: authError } = await userClient.auth.getUser();
 const subject = authData.user;
 if (authError || !subject) return Response.json({ error: "unauthorized" }, { status: 401, headers });
 let input: { resource_id?: string; purpose?: string; scopes?: string[] };
 try { input = await req.json(); } catch { return Response.json({ error: "invalid_json" }, { status: 400, headers }); }
 const resourceId = input.resource_id, purpose = input.purpose?.trim(), scopes = input.scopes;
 if (!resourceId || !purpose || !Array.isArray(scopes) || scopes.length === 0 || scopes.some((s) => typeof s !== "string" || !s.trim()))
  return Response.json({ error: "resource_id_purpose_and_scopes_required" }, { status: 400, headers });
 const admin = createClient(url, service, { auth: { persistSession: false } });
 const { data: resource, error: resourceError } = await admin.from("vac_resources").select("id,owner_id,name,content").eq("id", resourceId).maybeSingle();
 let grant: any = null, denial = "resource_not_found";
 if (resource && !resourceError) {
  denial = "no_matching_active_grant";
  const { data: grants } = await admin.from("vac_grants").select("id,owner_id,subject_user_id,scopes,purpose,expires_at,revoked_at")
   .eq("resource_id", resourceId).eq("subject_user_id", subject.id).eq("owner_id", resource.owner_id)
   .is("revoked_at", null).gt("expires_at", new Date().toISOString());
  grant = (grants ?? []).find((g: any) => g.purpose === purpose && scopes.every((s) => g.scopes.includes(s))) ?? null;
 }
 const allowed = Boolean(resource && grant);
 const { error: logError } = await admin.from("vac_access_log").insert({
  grant_id: grant?.id ?? null, resource_id: resource?.id ?? null,
  owner_id: resource?.owner_id ?? subject.id, subject_user_id: subject.id,
  purpose, requested_scopes: scopes, outcome: allowed ? "allowed" : "denied",
  reason: allowed ? "active_grant_scope_and_purpose_match" : denial
 });
 if (logError) return Response.json({ error: "audit_log_write_failed" }, { status: 503, headers });
 if (!allowed) return Response.json({ error: "access_denied", reason: denial }, { status: 403, headers });
 return Response.json({ resource: { id: resource.id, name: resource.name, content: resource.content },
  authorization: { grant_id: grant.id, scopes, expires_at: grant.expires_at } }, { status: 200, headers });
});
