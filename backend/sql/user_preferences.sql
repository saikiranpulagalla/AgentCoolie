-- Personalization settings used by AgentCoolie prompts.
-- Run this in Supabase SQL Editor for the active project.

create extension if not exists pgcrypto;

create table if not exists public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id text not null unique,
  tone text not null default 'friendly',
  response_length text not null default 'moderate',
  formality text not null default 'medium',
  include_emojis boolean not null default false,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_preferences_tone_check check (tone in ('professional', 'casual', 'friendly', 'formal')),
  constraint user_preferences_response_length_check check (response_length in ('brief', 'moderate', 'detailed')),
  constraint user_preferences_formality_check check (formality in ('low', 'medium', 'high'))
);

alter table public.user_preferences
  add column if not exists tone text not null default 'friendly',
  add column if not exists response_length text not null default 'moderate',
  add column if not exists formality text not null default 'medium',
  add column if not exists include_emojis boolean not null default false,
  add column if not exists metadata jsonb not null default '{}'::jsonb,
  add column if not exists updated_at timestamptz not null default now();

with ranked as (
  select
    id,
    row_number() over (
      partition by user_id
      order by updated_at desc nulls last, created_at desc nulls last, id desc
    ) as rn
  from public.user_preferences
  where user_id is not null
)
delete from public.user_preferences p
using ranked r
where p.id = r.id
  and r.rn > 1;

create index if not exists user_preferences_user_id_idx
  on public.user_preferences (user_id);

create unique index if not exists user_preferences_user_id_unique_idx
  on public.user_preferences (user_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists user_preferences_set_updated_at on public.user_preferences;
create trigger user_preferences_set_updated_at
  before update on public.user_preferences
  for each row
  execute function public.set_updated_at();

alter table public.user_preferences enable row level security;

drop policy if exists "Users can read own preferences" on public.user_preferences;
create policy "Users can read own preferences"
  on public.user_preferences
  for select
  using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own preferences" on public.user_preferences;
create policy "Users can insert own preferences"
  on public.user_preferences
  for insert
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can update own preferences" on public.user_preferences;
create policy "Users can update own preferences"
  on public.user_preferences
  for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);
