-- Tasks table and runtime execution state for scheduled tasks/reminders.

create extension if not exists pgcrypto;

create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  title text not null,
  description text,
  type text not null default 'general',
  priority text not null default 'medium',
  due_date timestamptz,
  completed boolean not null default false,
  status text not null default 'pending',
  execution_message text,
  last_attempt_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.tasks
  add column if not exists user_id text,
  add column if not exists title text,
  add column if not exists description text,
  add column if not exists type text not null default 'general',
  add column if not exists priority text not null default 'medium',
  add column if not exists due_date timestamptz,
  add column if not exists completed boolean not null default false,
  add column if not exists status text not null default 'pending',
  add column if not exists execution_message text,
  add column if not exists last_attempt_at timestamptz,
  add column if not exists metadata jsonb not null default '{}'::jsonb,
  add column if not exists created_at timestamptz not null default now(),
  add column if not exists updated_at timestamptz not null default now();

update public.tasks
set status = case when completed then 'sent' else 'pending' end
where status is null
   or status in ('completed', 'in_progress', 'cancelled');

create index if not exists tasks_user_id_idx
  on public.tasks (user_id);

create index if not exists tasks_user_status_due_idx
  on public.tasks (user_id, status, due_date);

create index if not exists tasks_status_due_idx
  on public.tasks (status, due_date);

alter table public.tasks enable row level security;

drop policy if exists "Users can read own tasks" on public.tasks;
create policy "Users can read own tasks"
  on public.tasks
  for select
  using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own tasks" on public.tasks;
create policy "Users can insert own tasks"
  on public.tasks
  for insert
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can update own tasks" on public.tasks;
create policy "Users can update own tasks"
  on public.tasks
  for update
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);

drop policy if exists "Users can delete own tasks" on public.tasks;
create policy "Users can delete own tasks"
  on public.tasks
  for delete
  using (auth.uid()::text = user_id);
