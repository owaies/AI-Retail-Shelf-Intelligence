alter table analyses add column if not exists image_width integer;
alter table analyses add column if not exists image_height integer;
alter table analyses add column if not exists model_name text;
alter table analyses add column if not exists model_version text;
alter table analyses add column if not exists object_coverage numeric(7,6) check (object_coverage is null or (object_coverage >= 0 and object_coverage <= 1));

create index if not exists idx_analyses_user_status on analyses(user_id, status, created_at desc);
