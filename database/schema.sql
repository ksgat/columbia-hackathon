-- ============================================================
-- PROPHECY DATABASE SCHEMA
-- Complete schema for social prediction markets
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    clout_score FLOAT DEFAULT 1000.0,        -- ELO-style rating
    clout_rank TEXT DEFAULT 'Silver',         -- Derived label
    total_bets_placed INTEGER DEFAULT 0,
    total_bets_won INTEGER DEFAULT 0,
    total_markets_created INTEGER DEFAULT 0,
    streak_current INTEGER DEFAULT 0,         -- Current win streak
    streak_best INTEGER DEFAULT 0,            -- All-time best streak
    balance_virtual FLOAT DEFAULT 1000.0,     -- Starting virtual coins
    balance_cash FLOAT DEFAULT 0.0,           -- USD value of USDC balance (not used for now)
    wallet_address TEXT,                       -- Future: Privy embedded wallet
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ROOMS
-- ============================================================
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    join_code TEXT UNIQUE NOT NULL,            -- 6-char alphanumeric code
    creator_id UUID REFERENCES users(id),
    currency_mode TEXT NOT NULL DEFAULT 'virtual' CHECK (currency_mode IN ('virtual', 'cash')),
    min_bet FLOAT DEFAULT 10.0,
    max_bet FLOAT DEFAULT 500.0,
    rake_percent FLOAT DEFAULT 0.0,           -- 0 for virtual, 2-5 for cash
    prophet_persona TEXT DEFAULT 'default',    -- Future: personality options
    resolution_window_hours INTEGER DEFAULT 24,
    resolution_bond_required BOOLEAN DEFAULT FALSE,
    resolution_bond_amount FLOAT DEFAULT 0.0,
    max_members INTEGER DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MEMBERSHIPS (user <-> room relationship)
-- ============================================================
CREATE TABLE memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'participant' CHECK (role IN ('participant', 'spectator', 'admin')),
    coins_virtual FLOAT DEFAULT 500.0,        -- Room-specific virtual balance
    coins_earned_total FLOAT DEFAULT 0.0,
    joined_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, room_id)
);

-- ============================================================
-- MARKETS
-- ============================================================
CREATE TABLE markets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    creator_id UUID REFERENCES users(id),      -- NULL for Prophet-generated
    title TEXT NOT NULL,                        -- The prediction question
    description TEXT,                           -- Additional context
    category TEXT,                              -- e.g., 'sports', 'personal', 'academic', 'politics'

    -- Market type
    market_type TEXT NOT NULL DEFAULT 'standard' CHECK (market_type IN (
        'standard',    -- Normal yes/no market
        'whisper',     -- Anonymous creator
        'chained',     -- Part of a conditional chain
        'derivative'   -- Bet on odds/meta-conditions
    )),

    -- Chained market fields
    parent_market_id UUID REFERENCES markets(id),
    trigger_condition TEXT,                     -- e.g., 'parent_resolves_yes', 'parent_resolves_no'
    chain_depth INTEGER DEFAULT 0,             -- 0 = root, 1 = first child, etc.

    -- Derivative market fields
    reference_market_id UUID REFERENCES markets(id),
    threshold_condition TEXT,                   -- e.g., 'odds_yes >= 0.8', 'total_trades >= 20'
    threshold_deadline TIMESTAMPTZ,

    -- Odds and trading
    odds_yes FLOAT DEFAULT 0.5,                -- Current probability (0.0 to 1.0)
    odds_no FLOAT GENERATED ALWAYS AS (1.0 - odds_yes) STORED,
    total_pool FLOAT DEFAULT 0.0,              -- Total coins/money in market
    total_yes_shares FLOAT DEFAULT 0.0,
    total_no_shares FLOAT DEFAULT 0.0,
    lmsr_b FLOAT DEFAULT 100.0,               -- LMSR liquidity parameter

    -- Currency (inherited from room)
    currency_mode TEXT NOT NULL DEFAULT 'virtual' CHECK (currency_mode IN ('virtual', 'cash')),

    -- Status and resolution
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN (
        'pending',     -- Created but not yet active (for chained markets awaiting trigger)
        'active',      -- Open for trading
        'voting',      -- Trading closed, community voting in progress
        'disputed',    -- No supermajority, Prophet reviewing
        'resolved',    -- Final outcome determined
        'cancelled'    -- Voided, all bets returned
    )),
    resolution_result TEXT CHECK (resolution_result IN ('yes', 'no', NULL)),
    resolution_method TEXT CHECK (resolution_method IN ('community', 'prophet', 'admin', NULL)),
    voting_deadline TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    expires_at TIMESTAMPTZ NOT NULL,           -- When trading closes and voting begins
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- TRADES
-- ============================================================
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),         -- NULL for Prophet's trades
    is_prophet_trade BOOLEAN DEFAULT FALSE,
    side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    amount FLOAT NOT NULL,                     -- Coins/USD spent
    shares_received FLOAT NOT NULL,            -- Shares received (from LMSR)
    odds_at_trade FLOAT NOT NULL,              -- Snapshot of odds_yes when trade was made
    currency TEXT NOT NULL DEFAULT 'virtual' CHECK (currency IN ('virtual', 'cash')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- RESOLUTION VOTES
-- ============================================================
CREATE TABLE resolution_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    vote TEXT NOT NULL CHECK (vote IN ('yes', 'no')),
    bond_amount FLOAT DEFAULT 0.0,             -- For cash room serious mode
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(market_id, user_id)                 -- One vote per user per market
);

-- ============================================================
-- PROPHET BETS (Oracle's own positions)
-- ============================================================
CREATE TABLE prophet_bets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE UNIQUE,
    side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    confidence FLOAT NOT NULL,                 -- 0.0 to 1.0
    reasoning TEXT,                             -- Prophet's public explanation
    amount FLOAT NOT NULL,                     -- Virtual coins staked
    shares_received FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ANOMALY FLAGS (Manipulation Detection)
-- ============================================================
CREATE TABLE anomaly_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    flagged_user_id UUID REFERENCES users(id), -- NULL if flagging a group pattern
    flag_type TEXT NOT NULL CHECK (flag_type IN (
        'large_last_minute_bet',
        'coordinated_same_direction',
        'sudden_reversal',
        'volume_spike',
        'vote_collusion'
    )),
    description TEXT NOT NULL,                 -- Prophet's commentary
    severity TEXT DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high')),
    trade_ids UUID[],                          -- Related trades
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- NARRATIVE EVENTS (Feed content generated by Prophet)
-- ============================================================
CREATE TABLE narrative_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'narrative_arc',        -- Storyline update
        'manipulation_alert',   -- Anomaly flag commentary
        'market_commentary',    -- General Prophet commentary
        'weekly_recap',         -- Weekly summary
        'achievement',          -- User badge/milestone
        'rivalry_update',       -- Head-to-head tracking
        'prophet_challenge',    -- Prophet calling someone out
        'resolution_commentary' -- Post-resolution analysis
    )),
    title TEXT,
    content TEXT NOT NULL,                      -- The actual narrative text
    related_user_ids UUID[],                   -- Users mentioned
    related_market_id UUID REFERENCES markets(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- WHISPER SUBMISSIONS
-- ============================================================
CREATE TABLE whispers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    submitter_id UUID REFERENCES users(id),    -- Stored for moderation, never exposed
    market_title TEXT NOT NULL,
    market_description TEXT,
    reveal_after_resolution BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    resulting_market_id UUID REFERENCES markets(id), -- If approved
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- USER ACHIEVEMENTS / BADGES
-- ============================================================
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    room_id UUID REFERENCES rooms(id),
    badge_type TEXT NOT NULL,                  -- See badge definitions in spec
    earned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, room_id, badge_type)
);

-- ============================================================
-- INDEXES for performance
-- ============================================================
CREATE INDEX idx_markets_room ON markets(room_id);
CREATE INDEX idx_markets_status ON markets(status);
CREATE INDEX idx_markets_parent ON markets(parent_market_id);
CREATE INDEX idx_markets_reference ON markets(reference_market_id);
CREATE INDEX idx_trades_market ON trades(market_id);
CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_created ON trades(created_at);
CREATE INDEX idx_memberships_user ON memberships(user_id);
CREATE INDEX idx_memberships_room ON memberships(room_id);
CREATE INDEX idx_resolution_votes_market ON resolution_votes(market_id);
CREATE INDEX idx_narrative_events_room ON narrative_events(room_id, created_at DESC);
CREATE INDEX idx_anomaly_flags_market ON anomaly_flags(market_id);

-- ============================================================
-- Enable Row Level Security (RLS) - Basic setup
-- We'll configure policies as needed
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE resolution_votes ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- SEED: Create Prophet User
-- Prophet is a special user that participates in markets
-- ============================================================
INSERT INTO users (id, email, display_name, avatar_url, clout_score, clout_rank)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'prophet@prophecy.ai',
    'Prophet',
    'https://api.dicebear.com/7.x/bottts/svg?seed=prophet',
    1000.0,
    'Oracle'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- SUCCESS!
-- ============================================================
-- Run this script in Supabase SQL Editor
-- All tables, indexes, and Prophet user created
