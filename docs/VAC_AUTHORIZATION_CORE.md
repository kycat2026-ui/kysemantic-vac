# VAC Authorization Core — Development

This is the first implementation slice for VAC's user-data-sovereignty goal. It is isolated from the NFT/persona prototype and does not touch other Supabase projects.

## Implemented design
- A user owns a resource in vac_resources.
- The owner issues a grant to one authenticated user with an exact purpose, scopes, and expiry.
- The owner revokes a grant by setting revoked_at or deleting it.
- The Edge Function validates the caller JWT and checks subject, resource owner, exact purpose, requested-scope subset, expiry, and revocation.
- Every authorization attempt is recorded in vac_access_log. Direct table access is owner-only under RLS.

## Not production-ready yet
- This is a development foundation, not a security-audited release.
- The gateway currently returns the full resource JSON after a matching grant; it does not yet filter individual JSON fields by scope. Do not store sensitive real data in this prototype.
- The Edge Function has not been deployed because the account reached its two-active-free-project limit. No existing project was modified.
- Rate limiting, field-level filtering, strict schema validation, abuse monitoring, and independent security review remain required.
- No blockchain deployment is required for this authorization path.

## Deployment when a dedicated project is available
1. Create a dedicated VAC Supabase project.
2. Apply supabase/migrations/20261123000100_vac_authorization_core.sql.
3. Deploy supabase/functions/vac-authorize/index.ts.
4. Configure SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY as Edge Function secrets. Never expose the service-role key to clients.
5. Run the owner/grantee/revocation/expiry/bypass integration tests before real data is admitted.

## Request
POST /functions/v1/vac-authorize

Request JSON fields: resource_id (UUID), purpose (string), scopes (string array). The caller must be authenticated. The grant must target that user's auth UUID, match the purpose exactly, include every requested scope, be unexpired, and not be revoked.