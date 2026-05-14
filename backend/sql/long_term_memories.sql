-- Long-term memory facts selected by the assistant.
-- Run this in Supabase SQL Editor for the active project.

create extension if not exists pgcrypto;

create table if not exists public.long_term_memories (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  content text not null,
  normalized_content text,
  source text not null default 'chat',
  importance_score numeric(3, 2) not null default 0.70,
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.long_term_memories
  add column if not exists normalized_content text;

create index if not exists long_term_memories_user_created_idx
  on public.long_term_memories (user_id, created_at desc);

create index if not exists long_term_memories_user_importance_idx
  on public.long_term_memories (user_id, importance_score desc);

update public.long_term_memories
set normalized_content = regexp_replace(lower(trim(content)), '[.!?]+$', '')
where normalized_content is null;

with ranked as (
  select
    id,
    row_number() over (
      partition by user_id, normalized_content
      order by created_at asc, id asc
    ) as rn
  from public.long_term_memories
  where normalized_content is not null
)
delete from public.long_term_memories m
using ranked r
where m.id = r.id
  and r.rn > 1;

create unique index if not exists long_term_memories_user_normalized_unique_idx
  on public.long_term_memories (user_id, normalized_content)
  where normalized_content is not null;

alter table public.long_term_memories enable row level security;

drop policy if exists "Users can read own long-term memories" on public.long_term_memories;
create policy "Users can read own long-term memories"
  on public.long_term_memories
  for select
  using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own long-term memories" on public.long_term_memories;
create policy "Users can insert own long-term memories"
  on public.long_term_memories
  for insert
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can update own long-term memories" on public.long_term_memories;
create policy "Users can update own long-term memories"
  on public.long_term_memories
  for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can delete own long-term memories" on public.long_term_memories;
create policy "Users can delete own long-term memories"
  on public.long_term_memories
  for delete
  using (auth.uid()::text = user_id);
