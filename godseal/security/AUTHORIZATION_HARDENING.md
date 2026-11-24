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
- Update the browser widget to use Supabase Auth sign-in and send `Authorization: Bearer <access_token>` on save. Do not store service-role credentials in browser code.
- Keep `verify_jwt=false` only if the function intentionally performs its own token validation for protected routes; alternatively turn it on only after public routes and browser API-key behavior are verified.
- Add integration tests: anonymous save=401; invalid JWT=401; authenticated save=201/private; forged owner ID ignored/rejected; anonymous private read=404; owner private read=200; other user private read=404; public read returns only approved public fields.

## Database migration

The sibling migration adds owner-scoped SELECT and private INSERT policies while retaining the existing public SELECT policy. This is defense in depth only: it does not protect requests made with the service-role key. The Edge Function authorization checks are mandatory.

## Release gate

This branch is a staging artifact. No production migration or Edge Function deployment has been run. Before release, complete the Edge Function and widget changes, run tests against a non-production database, inspect the diff, then obtain explicit approval for production deployment.
