-- Run in your Supabase project's SQL editor. Only the server service-role key
-- may access these records. Never put that key in the browser or repository.
create table if not exists public.rageval_records (
  id text primary key,
  kind text not null check (kind in ('dataset', 'trace', 'run')),
  body jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.rageval_records enable row level security;
revoke all on public.rageval_records from anon, authenticated;
grant all on public.rageval_records to service_role;
