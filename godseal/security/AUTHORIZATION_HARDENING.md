# GodSeal AI authorization hardening

Target project: `godseal-ai` (`lsxpcvaitgtskyogligj`)
Observed deployed function: `godseal-api`, version 2, `verify_jwt=false`
Observed source fingerprint: `6e961afe9987509fdd830f14ba9bc482cf9788f5fe6e990c0fbd9fe043d029ae`

## Confirmed findings from the deployed source

1. `POST /creations` inserts through a service-role client without authenticating the caller or setting `user_id`. The request's `visibility` value can select public visibility.
2. `GET /creations/:id` selects prompt and generated content by UUID only, without checking visibility or owner.
3. The table has RLS enabled, but the only observed SELECT policy is `visibility = 'public'` for anon/authenticated. The Edge Function uses the service-role key, which bypasses RLS.
4. The published widget sends no Authorization header when saving. Enforcing auth at the API without updating the client would break Save.

## Patch strategy

- Keep `GET /sigils` and `POST /interpret` public.
- For `POST /creations`, require a Bearer token and validate it with a Supabase client configured with the anon key using `auth.getUser(token)`. Reject absent/invalid tokens with 401. Derive `user_id` only from the returned user ID. Never accept a client-supplied owner ID. Force `visibility='private'` on creation.
- For `GET /creations/:id`, read visibility and owner. Return a public-safe projection for public rows. For private rows, require a valid JWT and matching owner ID; return the same generic 404 for missing and non-owner private rows.
- Implemented on this branch: the browser widget loads Supabase JS, supports email/password sign-up, sign-in and sign-out, and sends `Authorization: Bearer <access_token>` on save. The publishable key in browser code is intended to be public; never place a service-role key in browser code.
- Email confirmation behavior follows the Supabase project's Auth settings. If confirmations are enabled, users must verify their email before signing in.
- The API validates the bearer token using the project's `SUPABASE_ANON_KEY` and `auth.getUser(token)`; confirm the standard Edge Function environment variable is available before deploying.
- Keep `verify_jwt=false` only if the function intentionally performs its own token validation for protected routes; alternatively turn it on only after public routes and browser API-key behavior are verified.
- Add integration tests: anonymous save=401; invalid JWT=401; authenticated save=201/private; forged owner ID ignored/rejected; anonymous private read=404; owner private read=200; other user private read=404; public read returns only approved public fields.

## Database migration

The sibling migration adds owner-scoped SELECT and private INSERT policies while retaining the existing public SELECT policy. This is defense in depth only: it does not protect requests made with the service-role key. The Edge Function authorization checks are mandatory.

## Current staged implementation

- `supabase/functions/godseal-api/index.ts`: requires verified Supabase Auth identity for saves, derives `user_id` from the verified user, forces new rows private, hides private rows from non-owners with a generic 404, and returns an allowlisted projection for public rows.
- `godseal/godseal-ai-widget.js`: adds email/password Auth UI and attaches the current access token to save requests.
- `godseal/ai.html`: loads the Supabase JS UMD client before the widget.
- The function intentionally retains `verify_jwt=false` so anonymous `/interpret` and catalog routes continue to work; the protected creation routes validate their own bearer tokens. Do not switch gateway JWT verification on without checking anonymous-route compatibility.

## Release gate

This branch is a review artifact. No production migration or Edge Function deployment has been run. A separate Supabase development branch is not created yet. Before release, create a non-production database branch (cost approval may be required), apply the migration there, deploy the function and widget to a staging site, run the regression suite, inspect the diff, then obtain explicit approval for production deployment.

Legacy rows with `visibility='private'` and null `user_id` will remain inaccessible through the hardened API until ownership is deliberately reconciled. Do not bulk-publish them to work around this.
