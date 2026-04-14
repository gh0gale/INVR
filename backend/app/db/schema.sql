-- ==============================================================================
-- AI Investment Intelligence Platform — Schema Definition
-- Run this in your Supabase SQL Editor.
-- ==============================================================================

-- 1. Enable Extensions
create extension if not exists "vector" with schema public;

-- 2. Enums
create type public.income_bracket as enum ('<5L', '5L-10L', '10L-25L', '>25L');
create type public.risk_appetite as enum ('conservative', 'moderate', 'aggressive');
create type public.primary_goal as enum ('wealth_creation', 'retirement', 'child_education', 'short_term_growth');

-- 3. Tables

-- USER PROFILES (Layer 1)
create table public.user_profiles (
  id uuid references auth.users not null primary key,
  age integer not null check (age >= 18),
  income_bracket public.income_bracket,
  monthly_investable numeric default 0.0,
  risk_appetite public.risk_appetite not null,
  investment_horizon_months integer not null check (investment_horizon_months > 0),
  primary_goal public.primary_goal,
  sector_exposure jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- USER PERSONAS (Layer 2 - Computed)
create table public.user_personas (
  id uuid references public.user_profiles not null primary key,
  risk_score numeric(5,2) not null check (risk_score >= 0 and risk_score <= 100),
  persona_label text not null,
  preferred_sectors jsonb default '[]'::jsonb,
  sector_concentration_flags jsonb default '[]'::jsonb,
  diversification_score numeric(4,2) default 0.0,
  scoring_weight_profile jsonb not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- PORTFOLIO MODELS (Probabilistic State)
create table public.portfolio_models (
  user_id uuid references public.user_profiles not null primary key,
  sector_weight_ranges jsonb not null, -- E.g. {"IT": {"min": 0.40, "max": 0.55}}
  last_analyzed_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MARKET DATA (Stock Metrics Cache)
create table public.market_data (
  ticker text not null primary key,
  sector text,
  industry text,
  current_price numeric,
  -- Fundamentals
  trailing_eps numeric,
  revenue_growth_yoy numeric,
  revenue_cagr_3y numeric,
  net_profit_margin numeric,
  roe numeric,
  roce numeric,
  debt_to_equity numeric,
  free_cash_flow numeric,
  promoter_holding numeric,
  -- Technicals
  sma_20 numeric,
  sma_50 numeric,
  sma_200 numeric,
  rsi_14 numeric,
  macd_line numeric,
  macd_signal numeric,
  support_level numeric,
  resistance_level numeric,
  volume_ratio numeric,
  -- Valuations
  current_pe numeric,
  peg_ratio numeric,
  price_to_book numeric,
  ev_to_ebitda numeric,
  graham_number numeric,
  -- Risk
  beta_1y numeric,
  volatility_30d numeric,
  max_drawdown numeric,
  -- Timestamp
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- SECTOR BENCHMARKS
create table public.sector_benchmarks (
  sector_name text not null primary key,
  median_pe numeric not null,
  median_pb numeric not null,
  avg_roe numeric not null,
  concentration_threshold numeric not null, -- Alert if user exposure exceeds this
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MACRO CONTEXT
create table public.macro_context (
  id integer primary key default 1, -- Single row table
  rbi_repo_rate numeric,
  india_10y_bond_yield numeric,
  nifty_50_pe numeric,
  india_vix numeric,
  cpi_inflation numeric,
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- AI INVESTMENT THESES (Memory of past decisions)
create table public.ai_investment_theses (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.user_profiles not null,
  ticker text references public.market_data not null,
  action text not null,
  conviction_score int not null,
  recommended_allocation numeric,
  thesis_text text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RAG EMBEDDINGS (Knowledge Base)
create table public.rag_embeddings (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  metadata jsonb,
  embedding vector(384) -- all-MiniLM-L6-v2 produces 384-dimensional vectors
);

-- 4. Row Level Security (RLS) Triggers & Policies
alter table public.user_profiles enable row level security;
alter table public.user_personas enable row level security;
alter table public.portfolio_models enable row level security;
alter table public.ai_investment_theses enable row level security;

-- Users can only read/update their own profile
create policy "Users can view own profile" 
  on public.user_profiles for select 
  using ( auth.uid() = id );

create policy "Users can update own profile" 
  on public.user_profiles for update 
  using ( auth.uid() = id );

create policy "Users can view own persona" 
  on public.user_personas for select 
  using ( auth.uid() = id );

create policy "Users can view own portfolio models" 
  on public.portfolio_models for select 
  using ( auth.uid() = user_id );

create policy "Users can view own AI theses" 
  on public.ai_investment_theses for select 
  using ( auth.uid() = user_id );

-- Market data is public to all authenticated users
alter table public.market_data enable row level security;
create policy "Anyone can read market data" 
  on public.market_data for select 
  using ( true );

alter table public.sector_benchmarks enable row level security;
create policy "Anyone can read sector benchmarks" 
  on public.sector_benchmarks for select 
  using ( true );

alter table public.macro_context enable row level security;
create policy "Anyone can read macro context" 
  on public.macro_context for select 
  using ( true );

alter table public.rag_embeddings enable row level security;
create policy "Anyone can read rag embeddings" 
  on public.rag_embeddings for select 
  using ( true );
