-- Connected integration credentials, keyed by Firebase user id.

create extension if not exists pgcrypto;

create table if not exists public.user_credentials (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  type text not null,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, type)
);

alter table public.user_credentials
  add column if not exists user_id text,
  add column if not exists type text,
  add column if not exists data jsonb not null default '{}'::jsonb,
  add column if not exists created_at timestamptz not null default now(),
  add column if not exists updated_at timestamptz not null default now();

with ranked as (
  select
    id,
    row_number() over (
      partition by user_id, type
      order by updated_at desc nulls last, created_at desc nulls last, id desc
    ) as rn
  from public.user_credentials
  where user_id is not null
    and type is not null
)
delete from public.user_credentials c
using ranked r
where c.id = r.id
  and r.rn > 1;

create index if not exists user_credentials_user_type_idx
  on public.user_credentials (user_id, type);

create unique index if not exists user_credentials_user_type_unique_idx
  on public.user_credentials (user_id, type);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists user_credentials_set_updated_at on public.user_credentials;
create trigger user_credentials_set_updated_at
  before update on public.user_credentials
  for each row
  execute function public.set_updated_at();

alter table public.user_credentials enable row level security;

drop policy if exists "Users can read own credentials" on public.user_credentials;
create policy "Users can read own credentials"
  on public.user_credentials
  for select
  using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own credentials" on public.user_credentials;
create policy "Users can insert own credentials"
  on public.user_credentials
  for insert
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can update own credentials" on public.user_credentials;
create policy "Users can update own credentials"
  on public.user_credentials
  for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can delete own credentials" on public.user_credentials;
create policy "Users can delete own credentials"
  on public.user_credentials
  for delete
  using (auth.uid()::text = user_id);
