-- Runtime provider credentials for AgentCoolie.
-- Service-role backend reads this table. Normal app users should not get direct access.

create table if not exists public.app_secrets (
  key text primary key,
  value text not null,
  provider text,
  description text,
  is_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists app_secrets_set_updated_at on public.app_secrets;
create trigger app_secrets_set_updated_at
  before update on public.app_secrets
  for each row
  execute function public.set_updated_at();

alter table public.app_secrets enable row level security;

revoke all on table public.app_secrets from anon;
revoke all on table public.app_secrets from authenticated;
