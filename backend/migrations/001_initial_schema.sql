-- Retail application database isolation.
-- All objects live in a dedicated schema so shared Supabase public tables are untouched.
create schema if not exists retail_shelf_intelligence;
create extension if not exists pgcrypto;

create table if not exists retail_shelf_intelligence.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  created_at timestamptz not null default now()
);

create table if not exists retail_shelf_intelligence.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references retail_shelf_intelligence.users(id) on delete cascade,
  image_name text not null,
  image_storage_path text,
  status text not null check (status in ('processing', 'complete', 'partial', 'failed')),
  detection_count integer not null default 0 check (detection_count >= 0),
  image_width integer check (image_width is null or image_width > 0),
  image_height integer check (image_height is null or image_height > 0),
  model_name text,
  model_version text,
  object_coverage numeric(7,6) check (object_coverage is null or (object_coverage >= 0 and object_coverage <= 1)),
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists idx_retail_analyses_user_created_at
  on retail_shelf_intelligence.analyses(user_id, created_at desc);
create index if not exists idx_retail_analyses_status
  on retail_shelf_intelligence.analyses(status);
create index if not exists idx_retail_analyses_user_status
  on retail_shelf_intelligence.analyses(user_id, status, created_at desc);

create table if not exists retail_shelf_intelligence.detections (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references retail_shelf_intelligence.analyses(id) on delete cascade,
  class_name text not null,
  confidence numeric(5,4) not null check (confidence >= 0 and confidence <= 1),
  x numeric(12,4) not null check (x >= 0),
  y numeric(12,4) not null check (y >= 0),
  width numeric(12,4) not null check (width >= 0),
  height numeric(12,4) not null check (height >= 0),
  created_at timestamptz not null default now()
);
create index if not exists idx_retail_detections_analysis
  on retail_shelf_intelligence.detections(analysis_id);

create table if not exists retail_shelf_intelligence.shelf_regions (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references retail_shelf_intelligence.analyses(id) on delete cascade,
  label text not null,
  status text not null check (status in ('normal', 'low_stock', 'empty', 'unknown')),
  confidence numeric(5,4) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  x numeric(12,4) not null check (x >= 0),
  y numeric(12,4) not null check (y >= 0),
  width numeric(12,4) not null check (width >= 0),
  height numeric(12,4) not null check (height >= 0),
  created_at timestamptz not null default now()
);
create index if not exists idx_retail_shelf_regions_analysis
  on retail_shelf_intelligence.shelf_regions(analysis_id);

alter table retail_shelf_intelligence.users enable row level security;
alter table retail_shelf_intelligence.analyses enable row level security;
alter table retail_shelf_intelligence.detections enable row level security;
alter table retail_shelf_intelligence.shelf_regions enable row level security;

drop policy if exists retail_users_self on retail_shelf_intelligence.users;
create policy retail_users_self on retail_shelf_intelligence.users
  for select using (id = auth.uid());

drop policy if exists retail_analyses_owner on retail_shelf_intelligence.analyses;
create policy retail_analyses_owner on retail_shelf_intelligence.analyses
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists retail_detections_owner on retail_shelf_intelligence.detections;
create policy retail_detections_owner on retail_shelf_intelligence.detections
  for all using (
    exists (
      select 1 from retail_shelf_intelligence.analyses a
      where a.id = analysis_id and a.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from retail_shelf_intelligence.analyses a
      where a.id = analysis_id and a.user_id = auth.uid()
    )
  );

drop policy if exists retail_shelf_regions_owner on retail_shelf_intelligence.shelf_regions;
create policy retail_shelf_regions_owner on retail_shelf_intelligence.shelf_regions
  for all using (
    exists (
      select 1 from retail_shelf_intelligence.analyses a
      where a.id = analysis_id and a.user_id = auth.uid()
    )
  ) with check (
    exists (
      select 1 from retail_shelf_intelligence.analyses a
      where a.id = analysis_id and a.user_id = auth.uid()
    )
  );
