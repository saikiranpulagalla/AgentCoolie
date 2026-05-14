-- Optional chat-message conversation scope for durable history.
-- Existing deployments that do not have chat_messages yet can skip this until
-- the base chat_messages table has been created.

do $$
begin
  if to_regclass('public.chat_messages') is not null then
    alter table public.chat_messages
      add column if not exists conversation_id text;

    create index if not exists chat_messages_user_conversation_created_idx
      on public.chat_messages (user_id, conversation_id, created_at desc);
  end if;
end $$;
