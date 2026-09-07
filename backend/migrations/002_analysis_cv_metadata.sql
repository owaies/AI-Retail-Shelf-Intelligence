-- Idempotent metadata migration for the isolated retail schema.
alter table if exists retail_shelf_intelligence.analyses
  add column if not exists image_width integer;
alter table if exists retail_shelf_intelligence.analyses
  add column if not exists image_height integer;
alter table if exists retail_shelf_intelligence.analyses
  add column if not exists model_name text;
alter table if exists retail_shelf_intelligence.analyses
  add column if not exists model_version text;
alter table if exists retail_shelf_intelligence.analyses
  add column if not exists object_coverage numeric(7,6);

create index if not exists idx_retail_analyses_user_status
  on retail_shelf_intelligence.analyses(user_id, status, created_at desc);
