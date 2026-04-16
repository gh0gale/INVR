-- ==============================================================================
-- AI Investment Intelligence Platform — Clean Fresh Schema
-- Run this in your Supabase SQL Editor for a clean start.
-- ==============================================================================

-- 1. Enable Extensions
create extension if not exists "vector" with schema public;

-- 2. Enums
do $$ begin
  create type public.income_bracket as enum ('<5L', '5L-10L', '10L-25L', '>25L');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.risk_appetite as enum ('conservative', 'moderate', 'aggressive');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.primary_goal as enum ('wealth_creation', 'retirement', 'child_education', 'short_term_growth', 'dividend_income', 'portfolio_diversification');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.proficiency_level as enum ('beginner', 'intermediate', 'advanced');
exception when duplicate_object then null; end $$;

do $$ begin
  create type public.investment_horizon as enum ('intraday', 'swing', 'positional', 'long_term');
exception when duplicate_object then null; end $$;

-- 3. Tables

-- USER PROFILES
create table public.user_profiles (
  id uuid references auth.users not null primary key,
  age integer not null check (age >= 18),
  income_bracket public.income_bracket,
  monthly_investable numeric default 0.0,
  risk_appetite public.risk_appetite not null,
  investment_horizon_months integer not null check (investment_horizon_months > 0),
  primary_goal public.primary_goal,
  sector_exposure jsonb default '{}'::jsonb,
  portfolio_size numeric default 0.0,
  proficiency_level public.proficiency_level default 'beginner',
  investment_horizon public.investment_horizon default 'long_term',
  investment_amount_target numeric default 0.0,
  existing_holdings jsonb default '[]'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- USER PERSONAS
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

-- PORTFOLIO MODELS
create table public.portfolio_models (
  user_id uuid references public.user_profiles not null primary key,
  sector_weight_ranges jsonb not null,
  last_analyzed_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MARKET DATA (Complete Snapshot)
create table public.market_data (
  ticker text not null primary key,
  sector text,
  industry text,
  current_price numeric,
  -- Fundamentals
  trailing_eps numeric,
  forward_eps numeric,
  revenue_growth_yoy numeric,
  net_profit_margin numeric,
  roe numeric,
  roce numeric,
  debt_to_equity numeric,
  current_ratio numeric,
  free_cash_flow numeric,
  retained_earnings numeric,
  -- Technicals
  sma_50 numeric,
  sma_200 numeric,
  ema_50 numeric,
  ema_200 numeric,
  rsi_14 numeric,
  macd_line numeric,
  macd_signal numeric,
  bb_upper numeric,
  bb_lower numeric,
  bb_mid numeric,
  vwap_20d numeric,
  atr_14 numeric,
  -- Valuations
  current_pe numeric,
  forward_pe numeric,
  peg_ratio numeric,
  price_to_book numeric,
  ev_to_ebitda numeric,
  dividend_yield numeric,
  -- Risk & Quant
  beta_calc numeric,
  sharpe_ratio numeric,
  sortino_ratio numeric,
  volatility_30d numeric,
  max_drawdown numeric,
  var_95 numeric,
  -- Derivatives
  has_options boolean default false,
  put_call_ratio numeric,
  max_pain numeric,
  avg_implied_volatility numeric,
  -- Meta
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- SECTOR BENCHMARKS
create table public.sector_benchmarks (
  sector_name text not null primary key,
  median_pe numeric not null,
  median_pb numeric not null,
  avg_roe numeric not null,
  concentration_threshold numeric not null,
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- MACRO CONTEXT
create table public.macro_context (
  id integer primary key default 1,
  rbi_repo_rate numeric,
  india_10y_bond_yield numeric,
  nifty_50_pe numeric,
  india_vix numeric,
  cpi_inflation numeric,
  fii_dii_net text default 'neutral',
  last_updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- AI INVESTMENT THESES
create table public.ai_investment_theses (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.user_profiles not null,
  ticker text not null,
  action text not null,
  conviction_score int not null,
  recommended_allocation numeric,
  thesis_text text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RAG EMBEDDINGS
create table public.rag_embeddings (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  metadata jsonb,
  embedding vector(384)
);

-- 4. Enable RLS
alter table public.user_profiles enable row level security;
alter table public.user_personas enable row level security;
alter table public.portfolio_models enable row level security;
alter table public.ai_investment_theses enable row level security;
alter table public.market_data enable row level security;
alter table public.sector_benchmarks enable row level security;
alter table public.macro_context enable row level security;
alter table public.rag_embeddings enable row level security;

-- Policies (Simplified for dev)
create policy "Users can view own profile" on public.user_profiles for select using ( auth.uid() = id );
create policy "Anyone can read market data" on public.market_data for select using ( true );
create policy "Anyone can read sector benchmarks" on public.sector_benchmarks for select using ( true );
create policy "Anyone can read macro context" on public.macro_context for select using ( true );
create policy "Anyone can read rag embeddings" on public.rag_embeddings for select using ( true );
