-- VAC authorization core v0.1
create extension if not exists pgcrypto;
create table if not exists public.vac_resources (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references auth.users(id) on delete cascade,
 name text not null check (length(trim(name)) between 1 and 160),
 content jsonb not null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create table if not exists public.vac_grants (
 id uuid primary key default gen_random_uuid(),
 resource_id uuid not null references public.vac_resources(id) on delete cascade,
 owner_id uuid not null references auth.users(id) on delete cascade,
 subject_user_id uuid not null references auth.users(id) on delete cascade,
 scopes text[] not null check (cardinality(scopes) > 0),
 purpose text not null check (length(trim(purpose)) between 1 and 500),
 expires_at timestamptz not null,
 revoked_at timestamptz,
 created_at timestamptz not null default now(),
 constraint vac_grant_expiry_future check (expires_at > created_at)
);
create table if not exists public.vac_access_log (
 id bigint generated always as identity primary key,
 grant_id uuid references public.vac_grants(id) on delete set null,
 resource_id uuid references public.vac_resources(id) on delete set null,
 owner_id uuid not null references auth.users(id) on delete cascade,
 subject_user_id uuid not null references auth.users(id) on delete cascade,
 purpose text not null,
 requested_scopes text[] not null,
 outcome text not null check (outcome in ('allowed','denied')),
 reason text not null,
 created_at timestamptz not null default now()
);
create index if not exists vac_resources_owner_idx on public.vac_resources(owner_id);
create index if not exists vac_grants_resource_subject_idx on public.vac_grants(resource_id, subject_user_id);
create index if not exists vac_grants_owner_idx on public.vac_grants(owner_id);
create index if not exists vac_access_log_owner_created_idx on public.vac_access_log(owner_id, created_at desc);
create index if not exists vac_access_log_subject_created_idx on public.vac_access_log(subject_user_id, created_at desc);
alter table public.vac_resources enable row level security;
alter table public.vac_grants enable row level security;
alter table public.vac_access_log enable row level security;
drop policy if exists vac_resources_owner_select on public.vac_resources;
create policy vac_resources_owner_select on public.vac_resources for select to authenticated using (owner_id = (select auth.uid()));
drop policy if exists vac_resources_owner_insert on public.vac_resources;
create policy vac_resources_owner_insert on public.vac_resources for insert to authenticated with check (owner_id = (select auth.uid()));
drop policy if exists vac_resources_owner_update on public.vac_resources;
create policy vac_resources_owner_update on public.vac_resources for update to authenticated using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
drop policy if exists vac_resources_owner_delete on public.vac_resources;
create policy vac_resources_owner_delete on public.vac_resources for delete to authenticated using (owner_id = (select auth.uid()));
drop policy if exists vac_grants_owner_select on public.vac_grants;
create policy vac_grants_owner_select on public.vac_grants for select to authenticated using (owner_id = (select auth.uid()));
drop policy if exists vac_grants_owner_insert on public.vac_grants;
create policy vac_grants_owner_insert on public.vac_grants for insert to authenticated with check (
 owner_id = (select auth.uid()) and exists (
  select 1 from public.vac_resources r where r.id = resource_id and r.owner_id = (select auth.uid())
 )
);
drop policy if exists vac_grants_owner_update on public.vac_grants;
create policy vac_grants_owner_update on public.vac_grants for update to authenticated using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
drop policy if exists vac_grants_owner_delete on public.vac_grants;
create policy vac_grants_owner_delete on public.vac_grants for delete to authenticated using (owner_id = (select auth.uid()));
drop policy if exists vac_access_log_owner_select on public.vac_access_log;
create policy vac_access_log_owner_select on public.vac_access_log for select to authenticated using (owner_id = (select auth.uid()));
revoke all on public.vac_resources, public.vac_grants, public.vac_access_log from anon, authenticated;
grant select, insert, update, delete on public.vac_resources, public.vac_grants to authenticated;
grant select on public.vac_access_log to authenticated;
grant usage, select on sequence public.vac_access_log_id_seq to service_role;
grant all on public.vac_resources, public.vac_grants, public.vac_access_log to service_role;
