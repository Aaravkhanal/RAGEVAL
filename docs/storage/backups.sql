-- A single database statement sees a consistent application-data snapshot.
create or replace function public.rageval_snapshot() returns jsonb
language sql stable security definer set search_path=public as $$
 select jsonb_build_object('schema','rageval.logical_backup.v1','tables',jsonb_build_object(
 'rageval_records',coalesce((select jsonb_agg(to_jsonb(r) order by id) from rageval_records r),'[]'::jsonb),
 'rageval_jobs',coalesce((select jsonb_agg(to_jsonb(j) order by id) from rageval_jobs j),'[]'::jsonb)),
 'note','Consistent application-data snapshot. Supabase Auth identities and platform schemas are excluded.');
$$;
revoke execute on function public.rageval_snapshot() from public, anon, authenticated;
grant execute on function public.rageval_snapshot() to service_role;
