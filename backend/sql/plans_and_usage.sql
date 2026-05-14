-- AgentCoolie Companion/Autopilot plan state and usage accounting.
-- Run this in Supabase SQL Editor after the core tables.

create extension if not exists pgcrypto;

create table if not exists public.user_plans (
    user_id text primary key,
    plan text not null default 'companion'
        check (plan in ('companion', 'autopilot')),
    billing_status text not null default 'free'
        check (billing_status in ('free', 'trialing', 'active', 'past_due', 'canceled')),
    provider text,
    provider_customer_id text,
    provider_subscription_id text,
    current_period_start timestamptz,
    current_period_end timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.usage_events (
    id uuid primary key default gen_random_uuid(),
    user_id text not null,
    feature text not null,
    amount integer not null default 1 check (amount > 0),
    metadata jsonb not null default '{}'::jsonb,
    occurred_at timestamptz not null default now()
);

create index if not exists usage_events_user_feature_time_idx
    on public.usage_events (user_id, feature, occurred_at desc);

create index if not exists usage_events_user_time_idx
    on public.usage_events (user_id, occurred_at desc);

create or replace function public.consume_usage_quota(
    p_user_id text,
    p_feature text,
    p_amount integer,
    p_metadata jsonb default '{}'::jsonb,
    p_day_start timestamptz default null,
    p_day_limit integer default null,
    p_month_start timestamptz default null,
    p_month_limit integer default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_day_used integer := 0;
    v_month_used integer := 0;
    v_amount integer := greatest(1, coalesce(p_amount, 1));
begin
    perform pg_advisory_xact_lock(hashtextextended(p_user_id || ':' || p_feature, 0));

    if p_day_limit is not null then
        select coalesce(sum(amount), 0)
          into v_day_used
          from public.usage_events
         where user_id = p_user_id
           and feature = p_feature
           and occurred_at >= p_day_start;

        if v_day_used + v_amount > p_day_limit then
            return jsonb_build_object(
                'allowed', false,
                'period', 'day',
                'used', v_day_used,
                'limit', p_day_limit
            );
        end if;
    end if;

    if p_month_limit is not null then
        select coalesce(sum(amount), 0)
          into v_month_used
          from public.usage_events
         where user_id = p_user_id
           and feature = p_feature
           and occurred_at >= p_month_start;

        if v_month_used + v_amount > p_month_limit then
            return jsonb_build_object(
                'allowed', false,
                'period', 'month',
                'used', v_month_used,
                'limit', p_month_limit
            );
        end if;
    end if;

    insert into public.usage_events (user_id, feature, amount, metadata)
    values (p_user_id, p_feature, v_amount, coalesce(p_metadata, '{}'::jsonb));

    return jsonb_build_object(
        'allowed', true,
        'day_used', v_day_used + v_amount,
        'month_used', v_month_used + v_amount
    );
end;
$$;

revoke all on function public.consume_usage_quota(text, text, integer, jsonb, timestamptz, integer, timestamptz, integer) from anon;
revoke all on function public.consume_usage_quota(text, text, integer, jsonb, timestamptz, integer, timestamptz, integer) from authenticated;

create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists set_user_plans_updated_at on public.user_plans;
create trigger set_user_plans_updated_at
before update on public.user_plans
for each row execute function public.set_updated_at();

alter table public.user_plans enable row level security;
alter table public.usage_events enable row level security;

drop policy if exists "Users can read own plan" on public.user_plans;
create policy "Users can read own plan"
    on public.user_plans
    for select
    using (auth.uid()::text = user_id);

drop policy if exists "Users can read own usage" on public.usage_events;
create policy "Users can read own usage"
    on public.usage_events
    for select
    using (auth.uid()::text = user_id);

-- Plan writes should happen from the backend service role only.
-- Example manual upgrade:
-- insert into public.user_plans (user_id, plan, billing_status, current_period_start, current_period_end)
-- values ('firebase_uid_here', 'autopilot', 'active', now(), now() + interval '1 month')
-- on conflict (user_id) do update set
--     plan = excluded.plan,
--     billing_status = excluded.billing_status,
--     current_period_start = excluded.current_period_start,
--     current_period_end = excluded.current_period_end;
