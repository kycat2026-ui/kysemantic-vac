-- VAC authorization schema prototype.
-- Apply only to a dedicated VAC Supabase project, never to Shitocat or Godseal.
-- All tables are owner-scoped and RLS protected. No public access is granted.

create table if not exists public.vac_grants (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  subject_id text not null,
  resource text not null,
  purpose text not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  constraint vac_grants_nonempty_subject check (length(trim(subject_id)) > 0),
  constraint vac_grants_nonempty_resource check (length(trim(resource)) > 0),
  constraint vac_grants_nonempty_purpose check (length(trim(purpose)) > 0)
);

create index if not exists vac_grants_owner_active_idx
  on public.vac_grants(owner_id, expires_at)
  where revoked_at is null;

create table if not exists public.vac_audit_events (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  grant_id uuid references public.vac_grants(id) on delete set null,
  subject_id text not null,
  resource text not null,
  purpose text not null,
  decision text not null check (decision in ('ALLOW', 'DENY')),
  reason text not null,
  created_at timestamptz not null default now()
);

create index if not exists vac_audit_owner_created_idx
  on public.vac_audit_events(owner_id, created_at desc);

alter table public.vac_grants enable row level security;
alter table public.vac_audit_events enable row level security;

drop policy if exists "owner reads own VAC grants" on public.vac_grants;
create policy "owner reads own VAC grants"
  on public.vac_grants for select to authenticated
  using (owner_id = (select auth.uid()));

drop policy if exists "owner creates own VAC grants" on public.vac_grants;
create policy "owner creates own VAC grants"
  on public.vac_grants for insert to authenticated
  with check (owner_id = (select auth.uid()));

drop policy if exists "owner updates own VAC grants" on public.vac_grants;
create policy "owner updates own VAC grants"
  on public.vac_grants for update to authenticated
  using (owner_id = (select auth.uid()))
  with check (owner_id = (select auth.uid()));

drop policy if exists "owner reads own VAC audit" on public.vac_audit_events;
create policy "owner reads own VAC audit"
  on public.vac_audit_events for select to authenticated
  using (owner_id = (select auth.uid()));

-- Audit rows are intentionally not client-insertable or client-updatable.
-- A trusted server-side gateway should append audit events using a restricted
-- server credential after deriving owner_id from the verified grant.
