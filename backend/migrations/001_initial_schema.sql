create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  image_name text not null,
  image_storage_path text,
  status text not null check (status in ('processing', 'complete', 'partial', 'failed')),
  detection_count integer not null default 0 check (detection_count >= 0),
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists idx_analyses_user_created_at on analyses(user_id, created_at desc);
create index if not exists idx_analyses_status on analyses(status);

create table if not exists detections (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references analyses(id) on delete cascade,
  class_name text not null,
  confidence numeric(5,4) not null check (confidence >= 0 and confidence <= 1),
  x numeric(12,4) not null check (x >= 0),
  y numeric(12,4) not null check (y >= 0),
  width numeric(12,4) not null check (width >= 0),
  height numeric(12,4) not null check (height >= 0),
  created_at timestamptz not null default now()
);

create index if not exists idx_detections_analysis on detections(analysis_id);

create table if not exists shelf_regions (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references analyses(id) on delete cascade,
  label text not null,
  status text not null check (status in ('normal', 'low_stock', 'empty', 'unknown')),
  confidence numeric(5,4) check (confidence is null or (confidence >= 0 and confidence <= 1)),
  x numeric(12,4) not null check (x >= 0),
  y numeric(12,4) not null check (y >= 0),
  width numeric(12,4) not null check (width >= 0),
  height numeric(12,4) not null check (height >= 0),
  created_at timestamptz not null default now()
);

create index if not exists idx_shelf_regions_analysis on shelf_regions(analysis_id);
