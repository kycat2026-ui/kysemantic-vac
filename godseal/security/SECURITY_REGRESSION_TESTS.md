# GodSeal API security regression tests

Run only against a disposable Supabase staging project. Never run these against production data.

## Setup
- Create two Auth users: Alice and Bob.
- Obtain valid access tokens for both.
- Seed one private creation owned by Alice and one public creation.
- Ensure the Edge Function uses service role only for database operations and explicitly authorizes each request.

## Required assertions

| Case | Request | Expected |
|---|---|---|
| Anonymous save | POST /creations, no Authorization | 401 |
| Invalid token save | POST /creations, malformed/expired JWT | 401 |
| Alice save | POST /creations, Alice token | 201; stored user_id is Alice; visibility is private |
| Owner spoof | Alice token with body.user_id = Bob | 201 or 400; stored user_id must remain Alice |
| Public visibility spoof | Alice token with body.visibility = public | Stored row remains private |
| Anonymous private read | GET /creations/{Alice private id} | 404 |
| Bob reads Alice private | GET /creations/{Alice private id}, Bob token | 404 |
| Alice reads own private | GET /creations/{Alice private id}, Alice token | 200 |
| Anonymous public read | GET /creations/{public id} | 200; public-safe projection only |
| Bob reads public | GET /creations/{public id}, Bob token | 200; public-safe projection only |
| Anonymous interpret | POST /interpret | Existing anonymous behavior retained |
| Sigils catalog | GET /sigils | Existing public behavior retained |

## Public projection
Do not return `prompt`, `incantation`, `interpretation`, or arbitrary `metadata` for public rows unless product policy explicitly approves each field. Prefer an explicit allowlist such as `id,title,sigil_sequence,status,created_at`.

## Release checks
- Confirm CORS permits Authorization.
- Confirm browser widget obtains a user access token through Supabase Auth and sends it only on save.
- Confirm no service-role key or secret is present in browser assets.
- Verify function logs do not print bearer tokens or private creation bodies.
- Run the full suite against staging before production approval.
