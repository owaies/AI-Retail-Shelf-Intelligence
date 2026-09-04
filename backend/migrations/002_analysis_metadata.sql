-- Day 2 follow-up: align the database schema with the persisted analysis metadata.
-- Safe to run after 001_initial_schema.sql; all ALTERs are idempotent.

alter table if exists analyses
  add column if not exists image_width integer,
  add column if not exists image_height integer,
  add column if not exists model_name text,
  add column if not exists model_version text,
  add column if not exists object_coverage numeric(6,5);

alter table if exists analyses
  add constraint analyses_image_width_positive check (image_width is null or image_width > 0),
  add constraint analyses_image_height_positive check (image_height is null or image_height > 0),
  add constraint analyses_object_coverage_range check (
    object_coverage is null or (object_coverage >= 0 and object_coverage <= 1)
  );

create index if not exists idx_analyses_model on analyses(model_name, model_version);
