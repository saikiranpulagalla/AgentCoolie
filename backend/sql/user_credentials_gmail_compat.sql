-- Normalize existing Gmail credential JSON for n8n workflow compatibility.
-- The app stores provider credentials in user_credentials.data; n8n reads the same JSON.

update public.user_credentials
set data =
  data
  || case
    when type = 'gmail' and data ? 'client_id' and not (data ? 'gmail_client_id')
    then jsonb_build_object('gmail_client_id', data->>'client_id')
    else '{}'::jsonb
  end
  || case
    when type = 'gmail' and data ? 'client_secret' and not (data ? 'gmail_client_secret')
    then jsonb_build_object('gmail_client_secret', data->>'client_secret')
    else '{}'::jsonb
  end
  || case
    when type = 'gmail' and data ? 'refresh_token' and not (data ? 'gmail_refresh_token')
    then jsonb_build_object('gmail_refresh_token', data->>'refresh_token')
    else '{}'::jsonb
  end
  || case
    when type = 'gmail' and data ? 'token' and not (data ? 'gmail_access_token')
    then jsonb_build_object('gmail_access_token', data->>'token')
    else '{}'::jsonb
  end
where type = 'gmail';

create index if not exists user_credentials_data_gin_idx
  on public.user_credentials
  using gin (data);
