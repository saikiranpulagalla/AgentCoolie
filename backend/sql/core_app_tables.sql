-- Base durable tables used by the AgentCoolie backend.
-- Safe to run multiple times in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    firebase_id text not null unique,
    email text,
    display_name text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    conversation_id text,
    content text not null,
    role text not null check (role in ('user', 'assistant', 'system')),
    model text,
    attachments jsonb not null default '[]'::jsonb,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    title text not null,
    message text not null,
    type text not null default 'info',
    read boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists users_firebase_id_idx
    on public.users (firebase_id);

create index if not exists chat_messages_user_created_idx
    on public.chat_messages (user_id, created_at desc);

create index if not exists chat_messages_user_conversation_created_idx
    on public.chat_messages (user_id, conversation_id, created_at desc);

create index if not exists notifications_user_created_idx
    on public.notifications (user_id, created_at desc);

create index if not exists notifications_user_unread_idx
    on public.notifications (user_id, read, created_at desc);

create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists set_users_updated_at on public.users;
create trigger set_users_updated_at
before update on public.users
for each row execute function public.set_updated_at();

alter table public.users enable row level security;
alter table public.chat_messages enable row level security;
alter table public.notifications enable row level security;

drop policy if exists "Users can read own profile" on public.users;
create policy "Users can read own profile"
    on public.users
    for select
    using (auth.uid()::text = firebase_id);

drop policy if exists "Users can update own profile" on public.users;
create policy "Users can update own profile"
    on public.users
    for update
    using (auth.uid()::text = firebase_id)
    with check (auth.uid()::text = firebase_id);

drop policy if exists "Users can read own chat messages" on public.chat_messages;
create policy "Users can read own chat messages"
    on public.chat_messages
    for select
    using (auth.uid()::text = user_id);

drop policy if exists "Users can insert own chat messages" on public.chat_messages;
create policy "Users can insert own chat messages"
    on public.chat_messages
    for insert
    with check (auth.uid()::text = user_id);

drop policy if exists "Users can read own notifications" on public.notifications;
create policy "Users can read own notifications"
    on public.notifications
    for select
    using (auth.uid()::text = user_id);

drop policy if exists "Users can update own notifications" on public.notifications;
create policy "Users can update own notifications"
    on public.notifications
    for update
    using (auth.uid()::text = user_id)
    with check (auth.uid()::text = user_id);
