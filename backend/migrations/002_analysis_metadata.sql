-- Legacy Day 2 metadata migration retained for migration history.
-- The active schema is isolated under retail_shelf_intelligence.
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

create index if not exists idx_retail_analyses_model
  on retail_shelf_intelligence.analyses(model_name, model_version);
