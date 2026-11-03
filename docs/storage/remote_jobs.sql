create table if not exists public.rageval_jobs (
 id text primary key, config text not null, max_items integer not null check(max_items between 1 and 32),
 state text not null default 'queued', lease_until timestamptz, lease_token uuid,
 updated timestamptz not null default now(), payload jsonb
);
alter table public.rageval_jobs enable row level security;
revoke all on public.rageval_jobs from anon, authenticated;
grant all on public.rageval_jobs to service_role;
create or replace function public.rageval_enqueue(job_id text, config_name text, item_limit integer)
returns void language plpgsql security definer set search_path=public as $$
begin
 perform pg_advisory_xact_lock(724392);
 if exists(select 1 from rageval_jobs where state in ('queued','running')) then raise exception 'A job is already pending'; end if;
 insert into rageval_jobs(id,config,max_items) values(job_id,config_name,item_limit);
end $$;
create or replace function public.rageval_claim() returns jsonb
language plpgsql security definer set search_path=public as $$
declare claimed rageval_jobs;
begin
 perform pg_advisory_xact_lock(724392);
 if exists(select 1 from rageval_jobs where state='running' and lease_until>now()) then return null; end if;
 select * into claimed from rageval_jobs where state='queued' or (state='running' and lease_until<=now()) order by updated for update skip locked limit 1;
 if not found then return null; end if;
 update rageval_jobs set state='running',lease_token=gen_random_uuid(),lease_until=now()+interval '60 seconds',updated=now() where id=claimed.id returning * into claimed;
 return to_jsonb(claimed);
end $$;
create or replace function public.rageval_heartbeat(job_id text, lease uuid) returns void
language plpgsql security definer set search_path=public as $$ begin
 update rageval_jobs set lease_until=now()+interval '60 seconds',updated=now() where id=job_id and lease_token=lease and state='running' and lease_until>now();
end $$;
create or replace function public.rageval_finish(job_id text, lease uuid, final_state text, result_body jsonb) returns void
language plpgsql security definer set search_path=public as $$ begin
 if final_state not in ('complete','failed') then raise exception 'Invalid final state'; end if;
 update rageval_jobs set state=final_state,payload=result_body,updated=now(),lease_until=null where id=job_id and lease_token=lease and state='running' and lease_until>now();
 if not found then raise exception 'Lease lost'; end if;
end $$;
revoke execute on function public.rageval_enqueue(text,text,integer), public.rageval_claim(), public.rageval_heartbeat(text,uuid), public.rageval_finish(text,uuid,text,jsonb) from public, anon, authenticated;
grant execute on function public.rageval_enqueue(text,text,integer), public.rageval_claim(), public.rageval_heartbeat(text,uuid), public.rageval_finish(text,uuid,text,jsonb) to service_role;
-- Existing shared records stay in the admin namespace.
update public.rageval_records set body=jsonb_set(body,'{_owner}','"legacy-admin"') where not body ? '_owner';
