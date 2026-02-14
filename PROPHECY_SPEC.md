# PROPHECY — Complete Technical Specification

## Document Purpose

This document is a comprehensive, implementation-ready specification for **Prophecy**, a social prediction market web platform. It is written so that a senior AI coding agent (Claude Opus) can read this document top-to-bottom and build the entire application from scratch without ambiguity. Every feature, every API endpoint, every database table, every UI component, and every agent behavior is defined here.

---

## 1. Product Overview

### 1.1 One-Liner
Prophecy is a web platform where friend groups create private rooms, bet on anything using virtual coins or real money (USDC), and an AI agent named **Prophet** autonomously generates markets, sets odds, resolves bets via community voting, detects manipulation, and narrates the drama.

### 1.2 Core Value Proposition
People already make informal predictions and bets in friend groups. Prophecy formalizes this with a prediction market engine, layers in social dynamics (leaderboards, rivalries, anonymous bets), and makes it entertaining through an AI personality that actively participates as a market maker, commentator, and player.

### 1.3 Target Users
College students, friend groups, dorm floors, clubs, Discord communities — any social group of 4-50 people who enjoy friendly competition and banter.

### 1.4 Key Differentiators from Polymarket
- Private rooms (not public markets)
- AI agent (Prophet) that actively participates, generates markets, roasts users, and has its own betting score
- Social feed with narrative arcs, not a trading terminal
- Community jury resolution with 3/4 supermajority (resolution itself is a game)
- Conditional/chained markets, derivatives, whisper bets
- Dual currency (virtual + real money via USDC)

---

## 2. Tech Stack

### 2.1 Frontend
- **Framework**: React 18+ with Vite
- **Styling**: Tailwind CSS 3.x
- **Animations**: Framer Motion
- **Data Visualization**: Recharts (for odds charts, Vibe Check dashboard)
- **State Management**: Zustand (lightweight, minimal boilerplate)
- **Real-time**: Supabase JS client (real-time subscriptions)
- **Routing**: React Router v6
- **HTTP Client**: Axios or fetch
- **Wallet Auth**: Privy React SDK

### 2.2 Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0 with async support
- **Task Queue**: Celery with Redis broker (for background agent tasks, resolution timers)
- **WebSocket**: FastAPI WebSocket endpoints (for live ticker push)
- **AI SDK**: Anthropic Python SDK (Claude API with tool use)
- **Agent Orchestration**: LangGraph (for multi-agent coordination)

### 2.3 Database
- **Primary DB**: Supabase (PostgreSQL 15+)
- **Real-time**: Supabase Realtime (WebSocket subscriptions on tables)
- **Cache**: Redis (for session data, rate limiting, Celery broker)

### 2.4 Auth
- **Provider**: Supabase Auth with Google OAuth
- **Wallet**: Privy (creates embedded wallets via Google login — no MetaMask required)

### 2.5 Payments
- **Currency**: USDC on Base network
- **Testnet**: Base Sepolia for hackathon demo
- **Wallet Abstraction**: Privy embedded wallets
- **Smart Contract**: Simple escrow contract for holding market funds

### 2.6 Hosting
- **Frontend**: Vercel
- **Backend**: Railway
- **Database**: Supabase Cloud (free tier)
- **Redis**: Railway Redis addon or Upstash

---

## 3. Database Schema

### 3.1 Complete Table Definitions

All timestamps are `TIMESTAMPTZ` (UTC). All IDs are `UUID` with `gen_random_uuid()` default.

```sql
-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    clout_score FLOAT DEFAULT 1000.0,        -- ELO-style rating
    clout_rank TEXT DEFAULT 'Novice',          -- Derived label
    total_bets_placed INTEGER DEFAULT 0,
    total_bets_won INTEGER DEFAULT 0,
    total_markets_created INTEGER DEFAULT 0,
    streak_current INTEGER DEFAULT 0,          -- Current win streak
    streak_best INTEGER DEFAULT 0,             -- All-time best streak
    balance_virtual FLOAT DEFAULT 1000.0,      -- Starting virtual coins
    balance_cash FLOAT DEFAULT 0.0,            -- USD value of USDC balance
    wallet_address TEXT,                        -- Privy embedded wallet
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
    join_code TEXT UNIQUE NOT NULL,             -- 6-char alphanumeric code
    creator_id UUID REFERENCES users(id),
    currency_mode TEXT NOT NULL DEFAULT 'virtual' CHECK (currency_mode IN ('virtual', 'cash')),
    min_bet FLOAT DEFAULT 10.0,
    max_bet FLOAT DEFAULT 500.0,
    rake_percent FLOAT DEFAULT 0.0,            -- 0 for virtual, 2-5 for cash
    prophet_persona TEXT DEFAULT 'default',     -- Future: personality options
    resolution_window_hours INTEGER DEFAULT 24,
    resolution_bond_required BOOLEAN DEFAULT FALSE, -- Serious mode for cash rooms
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
    coins_virtual FLOAT DEFAULT 500.0,         -- Room-specific virtual balance
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
    creator_id UUID REFERENCES users(id),       -- NULL for Prophet-generated
    title TEXT NOT NULL,                         -- The prediction question
    description TEXT,                            -- Additional context
    category TEXT,                               -- e.g., 'sports', 'personal', 'academic', 'politics'

    -- Market type
    market_type TEXT NOT NULL DEFAULT 'standard' CHECK (market_type IN (
        'standard',    -- Normal yes/no market
        'whisper',     -- Anonymous creator
        'chained',     -- Part of a conditional chain
        'derivative'   -- Bet on odds/meta-conditions
    )),

    -- Chained market fields
    parent_market_id UUID REFERENCES markets(id),
    trigger_condition TEXT,                      -- e.g., 'parent_resolves_yes', 'parent_resolves_no'
    chain_depth INTEGER DEFAULT 0,              -- 0 = root, 1 = first child, etc.

    -- Derivative market fields
    reference_market_id UUID REFERENCES markets(id),
    threshold_condition TEXT,                    -- e.g., 'odds_yes >= 0.8', 'total_trades >= 20'
    threshold_deadline TIMESTAMPTZ,

    -- Odds and trading
    odds_yes FLOAT DEFAULT 0.5,                 -- Current probability (0.0 to 1.0)
    odds_no FLOAT GENERATED ALWAYS AS (1.0 - odds_yes) STORED,
    total_pool FLOAT DEFAULT 0.0,               -- Total coins/money in market
    total_yes_shares FLOAT DEFAULT 0.0,
    total_no_shares FLOAT DEFAULT 0.0,
    lmsr_b FLOAT DEFAULT 100.0,                -- LMSR liquidity parameter

    -- Currency (inherited from room)
    currency_mode TEXT NOT NULL DEFAULT 'virtual' CHECK (currency_mode IN ('virtual', 'cash')),

    -- Status and resolution
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending',     -- Created but not yet active (for chained markets awaiting trigger)
        'active',      -- Open for trading
        'voting',      -- Trading closed, community voting in progress
        'disputed',    -- No supermajority, Prophet reviewing
        'resolved',    -- Final outcome determined
        'cancelled'    -- Voided, all bets returned
    )),
    resolution_result TEXT CHECK (resolution_result IN ('yes', 'no', NULL)),
    resolution_method TEXT CHECK (resolution_method IN ('community', 'prophet', NULL)),
    voting_deadline TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    expires_at TIMESTAMPTZ NOT NULL,            -- When trading closes and voting begins
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- TRADES
-- ============================================================
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),          -- NULL for Prophet's trades
    is_prophet_trade BOOLEAN DEFAULT FALSE,
    side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    amount FLOAT NOT NULL,                      -- Coins/USD spent
    shares_received FLOAT NOT NULL,             -- Shares received (from LMSR)
    odds_at_trade FLOAT NOT NULL,               -- Snapshot of odds_yes when trade was made
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
    bond_amount FLOAT DEFAULT 0.0,              -- For cash room serious mode
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(market_id, user_id)                  -- One vote per user per market
);

-- ============================================================
-- PROPHET BETS (Oracle's own positions)
-- ============================================================
CREATE TABLE prophet_bets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE UNIQUE,
    side TEXT NOT NULL CHECK (side IN ('yes', 'no')),
    confidence FLOAT NOT NULL,                  -- 0.0 to 1.0
    reasoning TEXT,                              -- Prophet's public explanation
    amount FLOAT NOT NULL,                      -- Virtual coins staked
    shares_received FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ANOMALY FLAGS (Manipulation Detection)
-- ============================================================
CREATE TABLE anomaly_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market_id UUID REFERENCES markets(id) ON DELETE CASCADE,
    flagged_user_id UUID REFERENCES users(id),  -- NULL if flagging a group pattern
    flag_type TEXT NOT NULL CHECK (flag_type IN (
        'large_last_minute_bet',
        'coordinated_same_direction',
        'sudden_reversal',
        'volume_spike',
        'vote_collusion'
    )),
    description TEXT NOT NULL,                  -- Prophet's commentary
    severity TEXT DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high')),
    trade_ids UUID[],                           -- Related trades
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
    content TEXT NOT NULL,                       -- The actual narrative text
    related_user_ids UUID[],                    -- Users mentioned
    related_market_id UUID REFERENCES markets(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- WHISPER SUBMISSIONS
-- ============================================================
CREATE TABLE whispers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    submitter_id UUID REFERENCES users(id),     -- Stored for moderation, never exposed
    market_title TEXT NOT NULL,
    market_description TEXT,
    reveal_after_resolution BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    resulting_market_id UUID REFERENCES markets(id), -- If approved
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- DEPOSITS & WITHDRAWALS (Cash rooms only)
-- ============================================================
CREATE TABLE deposits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    amount_usdc FLOAT NOT NULL,
    tx_hash TEXT,
    chain TEXT DEFAULT 'base',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirming', 'complete', 'failed')),
    created_at TIMESTAMPTZ DEFAULT now(),
    confirmed_at TIMESTAMPTZ
);

CREATE TABLE withdrawals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    amount_usdc FLOAT NOT NULL,
    destination_address TEXT NOT NULL,
    tx_hash TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'complete', 'failed')),
    requested_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- ============================================================
-- USER ACHIEVEMENTS / BADGES
-- ============================================================
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    room_id UUID REFERENCES rooms(id),
    badge_type TEXT NOT NULL,                   -- See badge definitions below
    earned_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, room_id, badge_type)
);

-- ============================================================
-- INDEXES
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
```

### 3.2 Badge Definitions

These are the `badge_type` string values used in the `achievements` table. Check and award these after each market resolution:

| Badge | Condition |
|---|---|
| `oracle` | 5 correct predictions in a row |
| `degen` | 10 bets placed in a single day |
| `upset_king` | Won a bet placed at sub-20% odds |
| `contrarian` | Profited 3+ times betting against >70% consensus |
| `whale` | Single largest bet in room history |
| `paper_hands` | Switched sides on a market (sold and re-bought opposite) |
| `diamond_hands` | Held a losing position that ultimately won |
| `gaslighter` | Voted against reality 3+ times (vote didn't match outcome) |
| `prophet_slayer` | Beat Prophet's prediction 5+ times |
| `market_maker` | Created 10+ markets that got 5+ trades each |
| `silent_assassin` | Top 3 on leaderboard with fewest total bets |
| `streak_master` | Achieved a 10+ win streak |

### 3.3 Supabase Real-time Subscriptions

Enable real-time on these tables for live UI updates:

| Table | Events | Used For |
|---|---|---|
| `markets` | UPDATE (odds_yes, status) | Live Odds Ticker, Market Detail odds chart |
| `trades` | INSERT | Feed updates, ticker volume indicators |
| `narrative_events` | INSERT | Feed new cards |
| `resolution_votes` | INSERT | Vote count during resolution phase |
| `anomaly_flags` | INSERT | Manipulation alert cards |

---

## 4. API Endpoints

### 4.1 Auth

```
POST   /api/auth/login          — Google OAuth via Supabase, returns JWT + creates user if new
POST   /api/auth/logout         — Invalidate session
GET    /api/auth/me             — Get current user profile
```

### 4.2 Users

```
GET    /api/users/:id                    — Get user public profile
PATCH  /api/users/:id                    — Update display name, avatar
GET    /api/users/:id/portfolio          — Get all open positions across rooms
GET    /api/users/:id/achievements       — Get all badges
GET    /api/users/:id/stats              — Aggregate stats (win rate, avg return, etc.)
GET    /api/users/:id/hedge-suggestions  — Prophet's hedge mode suggestions
```

### 4.3 Rooms

```
POST   /api/rooms                       — Create room (body: name, description, currency_mode, min_bet, max_bet, rake_percent)
GET    /api/rooms                       — List rooms user is a member of
GET    /api/rooms/:id                   — Get room details + member count
POST   /api/rooms/:id/join              — Join room via join_code (body: join_code, role)
POST   /api/rooms/:id/leave             — Leave room
GET    /api/rooms/:id/leaderboard       — Get room leaderboard sorted by clout_score
GET    /api/rooms/:id/feed              — Get room feed (markets + narrative events, paginated, sorted by created_at DESC)
GET    /api/rooms/:id/vibe-check        — Get Vibe Check dashboard data (see Section 7.3)
GET    /api/rooms/:id/members           — List members with roles
PATCH  /api/rooms/:id/settings          — Update room settings (admin only)
```

### 4.4 Markets

```
POST   /api/markets                     — Create market (body: room_id, title, description, category, market_type, expires_at, parent_market_id, trigger_condition, reference_market_id, threshold_condition, threshold_deadline)
GET    /api/markets/:id                 — Get market detail (odds history, trade count, Prophet bet, chain children)
GET    /api/markets/:id/trades          — Get trade history for market (paginated)
GET    /api/markets/:id/chain           — Get full chain tree (parent + all descendants)
GET    /api/markets/:id/derivatives     — Get all derivative markets referencing this market
POST   /api/markets/:id/trade           — Place a trade (body: side, amount)
GET    /api/markets/:id/votes           — Get resolution vote tallies (individual votes hidden until deadline)
POST   /api/markets/:id/vote            — Cast resolution vote (body: vote)
POST   /api/markets/:id/cancel          — Cancel market (admin/creator only)
```

### 4.5 Whispers

```
POST   /api/rooms/:id/whispers          — Submit anonymous market (body: title, description, reveal_after_resolution)
GET    /api/rooms/:id/whispers/pending   — Get pending whispers (admin only, for moderation)
POST   /api/whispers/:id/approve         — Approve whisper → creates market (admin only)
POST   /api/whispers/:id/reject          — Reject whisper (admin only)
```

### 4.6 Payments (Cash Rooms)

```
POST   /api/payments/deposit            — Initiate USDC deposit (returns deposit address/instructions)
GET    /api/payments/deposit/:id/status  — Check deposit confirmation status
POST   /api/payments/withdraw           — Request withdrawal (body: amount, destination_address)
GET    /api/payments/balance             — Get user's cash balance
GET    /api/payments/history             — Get deposit/withdrawal history
```

### 4.7 Live Data (WebSocket)

```
WS     /ws/ticker/:room_id             — Live odds ticker stream for a room
WS     /ws/market/:market_id           — Live updates for a specific market (odds, trades, votes)
```

These WebSocket endpoints push events whenever Supabase real-time detects changes. The backend listens to Supabase subscriptions and fans out to connected WebSocket clients.

---

## 5. Trading Engine — LMSR (Logarithmic Market Scoring Rule)

### 5.1 Overview

LMSR is the same automated market maker used by Polymarket and prediction market research. It provides infinite liquidity (users can always trade) and deterministic pricing based on share quantities.

### 5.2 Core Math

The LMSR cost function determines the price of trades:

```python
import math

class LMSRMarketMaker:
    """
    Logarithmic Market Scoring Rule market maker.

    b = liquidity parameter. Higher b = more liquidity = less price impact per trade.
    For small rooms (5-20 people), b=100 works well.
    For larger rooms, scale b up proportionally.
    """

    def __init__(self, b: float = 100.0, yes_shares: float = 0.0, no_shares: float = 0.0):
        self.b = b
        self.yes_shares = yes_shares
        self.no_shares = no_shares

    def cost(self, yes_shares: float, no_shares: float) -> float:
        """Total cost function C(q_yes, q_no)"""
        return self.b * math.log(math.exp(yes_shares / self.b) + math.exp(no_shares / self.b))

    def current_price_yes(self) -> float:
        """Current price (probability) of YES shares"""
        exp_yes = math.exp(self.yes_shares / self.b)
        exp_no = math.exp(self.no_shares / self.b)
        return exp_yes / (exp_yes + exp_no)

    def current_price_no(self) -> float:
        """Current price (probability) of NO shares"""
        return 1.0 - self.current_price_yes()

    def cost_to_buy(self, side: str, num_shares: float) -> float:
        """
        Calculate the cost to buy `num_shares` of `side`.
        Returns the amount of coins/USD the user must pay.
        """
        old_cost = self.cost(self.yes_shares, self.no_shares)
        if side == 'yes':
            new_cost = self.cost(self.yes_shares + num_shares, self.no_shares)
        else:
            new_cost = self.cost(self.yes_shares, self.no_shares + num_shares)
        return new_cost - old_cost

    def execute_trade(self, side: str, amount: float) -> float:
        """
        Given an amount of coins/USD to spend, calculate shares received
        and update state. Returns number of shares received.

        Uses binary search to find the number of shares that costs `amount`.
        """
        low, high = 0.0, amount * 10  # Upper bound estimate
        for _ in range(100):  # Binary search iterations
            mid = (low + high) / 2
            cost = self.cost_to_buy(side, mid)
            if cost < amount:
                low = mid
            else:
                high = mid
        shares = (low + high) / 2

        # Update state
        if side == 'yes':
            self.yes_shares += shares
        else:
            self.no_shares += shares

        return shares

    def payout_per_share(self) -> float:
        """Each share pays out 1.0 if correct, 0.0 if wrong."""
        return 1.0
```

### 5.3 Trade Flow (Step by Step)

When a user places a trade via `POST /api/markets/:id/trade`:

1. **Validate**: Check market is `active`, user is a `participant` in the room, amount >= room's min_bet and <= max_bet, user has sufficient balance.
2. **Load LMSR state**: Instantiate `LMSRMarketMaker` with the market's current `lmsr_b`, `total_yes_shares`, `total_no_shares`.
3. **Execute trade**: Call `execute_trade(side, amount)` to get `shares_received`.
4. **Deduct balance**: Subtract `amount` from user's room balance (`memberships.coins_virtual` or `users.balance_cash`).
5. **Record trade**: Insert into `trades` table with all fields including `odds_at_trade` = current `odds_yes` before the trade.
6. **Update market**: Update `markets.total_yes_shares`, `markets.total_no_shares`, `markets.odds_yes` (= `current_price_yes()`), `markets.total_pool += amount`.
7. **Trigger anomaly detection**: Send trade event to the Commentary Agent for manipulation checking (async via Celery task).
8. **Trigger derivative check**: If any derivative markets reference this market, check if threshold conditions are now met (async).
9. **Return**: Respond with `{ shares_received, new_odds_yes, new_odds_no }`.

### 5.4 Payout Flow

When a market resolves:

1. Query all trades for the market.
2. For each trade on the winning side, calculate payout: `shares_received * 1.0` (each share pays 1 coin/dollar).
3. For cash rooms, apply rake: `payout = shares_received * (1 - rake_percent / 100)`.
4. Credit winnings to user's balance.
5. For cash rooms, add rake amount to platform revenue tracking.
6. Update user stats: `total_bets_won`, `streak_current`, `clout_score` (see Section 8).

---

## 6. Resolution System — Community Jury + Prophet Oversight

### 6.1 Resolution Flow (Complete)

```
Market's expires_at is reached
    │
    ▼
[1] Market status → 'voting'
    Trading is frozen (no new trades accepted)
    voting_deadline = now() + room.resolution_window_hours
    Push notification to all room participants: "Time to vote on: {title}"
    │
    ▼
[2] VOTING PHASE (default 24 hours)
    - Each participant (non-spectator) in the room can cast ONE vote: YES or NO
    - Votes are stored in resolution_votes table
    - UI shows total vote count but NOT individual votes or YES/NO split
    - In cash rooms with resolution_bond_required=true, voters must stake bond_amount
    - Spectators CANNOT vote
    │
    ▼
[3] VOTING DEADLINE REACHED
    - All individual votes are revealed simultaneously
    - Calculate: yes_count / total_votes and no_count / total_votes
    │
    ├── IF yes_count / total_votes >= 0.75 → Resolve YES
    ├── IF no_count / total_votes >= 0.75 → Resolve NO
    └── IF neither side >= 0.75 → Market enters 'disputed' status
        │
        ▼
[4] DISPUTE RESOLUTION (Prophet steps in)
    - Prophet Agent reviews: market title, description, web search for evidence,
      room context, vote distribution, trade patterns
    - Prophet produces a binding ruling with chain-of-thought reasoning
    - Reasoning is posted as a narrative_event (type: 'resolution_commentary')
    - Prophet's ruling is final
    │
    ▼
[5] POST-RESOLUTION
    - Payouts distributed (see Section 5.4)
    - In cash rooms with bonds: voters who voted AGAINST Prophet's ruling lose their bond
    - Clout scores updated for all participants
    - Prophet generates commentary narrative_event
    - Achievement checks run (streak updates, badge awards)
    - If this market is a parent in a chain, trigger child markets (see Section 7.1)
    - If any derivative markets reference this market, check resolution conditions
    │
    ▼
[6] CASH ROOM DISPUTE WINDOW (cash rooms only)
    - After resolution, winnings are locked for 6 hours before becoming withdrawable
    - During this window, if 2/3 of members flag the resolution, it reopens for re-vote
    - This prevents immediate cash-out on contested resolutions
```

### 6.2 Prophet Dispute Resolution Logic

When Prophet must break a dispute, the Resolution Agent should:

1. **Search the web** for objective evidence (sports scores, news, verifiable facts).
2. **Analyze the market context**: title, description, category, room history.
3. **Review vote distribution**: Who voted what, are there patterns suggesting collusion?
4. **Review trade positions**: Are voters aligned with their financial positions (conflict of interest)?
5. **Produce reasoning**: A 2-4 sentence chain-of-thought explanation visible to the room.
6. **Declare result**: YES or NO.

The Claude API call for dispute resolution should use tool use with a `web_search` tool and return structured JSON:

```json
{
    "ruling": "yes" | "no",
    "confidence": 0.0-1.0,
    "reasoning": "string — visible to users",
    "evidence_sources": ["url1", "url2"]
}
```

### 6.3 Vote Integrity Tracking

After each resolution, update a per-user honesty metric:

```python
# After each market resolves, for each voter:
vote_matched_outcome = (vote == resolution_result)
# Track in a running counter on user profile or separate table
# Feed into Narrative Arcs: "Sarah has voted against reality 6 times this month"
```

---

## 7. Advanced Features — Detailed Implementation

### 7.1 Conditional / Chained Markets

**Concept**: Markets linked in parent-child relationships. When a parent resolves, it can automatically activate child markets.

**Creation Flow**:
1. User (or Prophet) creates a root market as normal.
2. When creating a child market, set `parent_market_id` to the root's ID, `trigger_condition` to `'parent_resolves_yes'` or `'parent_resolves_no'`, and `status` to `'pending'`.
3. Child markets are visible in the UI (grayed out, showing "Activates if {parent title} resolves {condition}") but cannot be traded on.
4. When the parent resolves, a background task queries all children where `parent_market_id = resolved_market_id AND trigger_condition matches`. Matching children are set to `status = 'active'` with `expires_at` set to a reasonable window (e.g., 48 hours from activation).
5. Prophet sets opening odds on newly activated children.

**Chain Depth Limit**: Maximum 3 levels deep (root → child → grandchild) to prevent complexity explosion.

**UI Representation**: Display chains as a horizontal tree/flowchart. Each node is a market card. Lines connect parent to children with the trigger condition labeled on the line. Active markets are full color, pending markets are dimmed, resolved markets show their result.

**Prophet Auto-Chain Generation**: When Prophet generates a market, it should also consider generating 1-2 conditional follow-ups. The Market Gen Agent should output:

```json
{
    "root_market": { "title": "...", "odds_yes": 0.5 },
    "children": [
        { "title": "...", "trigger_condition": "parent_resolves_yes", "odds_yes": 0.6 },
        { "title": "...", "trigger_condition": "parent_resolves_no", "odds_yes": 0.4 }
    ]
}
```

### 7.2 Whisper Bets

**Concept**: Anonymous market submissions that Prophet posts on the creator's behalf.

**Flow**:
1. User taps "Whisper a Market" button in room.
2. Fills out: market title, optional description, toggle for "Reveal me after resolution."
3. Submission goes to `whispers` table with `status = 'pending'`.
4. Room admins see pending whispers in a moderation queue (separate UI tab).
5. Admin approves → a market is created with `market_type = 'whisper'`, `creator_id = NULL` in the public-facing API response (the real `creator_id` is set in the DB for backend moderation but the API endpoint for `GET /api/markets/:id` returns `creator: { type: 'whisper', display_name: 'Prophet Whisper' }` instead of the real user).
6. Admin rejects → whisper is marked rejected, submitter is notified.
7. If `reveal_after_resolution = true`, after the market resolves, the `creator_id` is unmasked in the API response and a narrative_event is posted: "The whisper about '{title}' was submitted by @{username}!"

**Auto-Approval Option**: Rooms can toggle auto-approve for whispers (skip moderation). Prophet still runs a basic content check before posting.

### 7.3 Vibe Check Dashboard

**Concept**: A real-time visualization showing the room's collective mood, belief state, and behavioral patterns.

**Data Aggregation** (computed server-side, returned by `GET /api/rooms/:id/vibe-check`):

```json
{
    "optimism_score": 0.65,            // Average odds_yes across active markets
    "divisiveness_score": 0.42,         // Average absolute deviation from 0.5
    "most_divisive_market": { ... },    // Market closest to 50/50
    "most_one_sided_market": { ... },   // Market furthest from 50/50
    "topic_distribution": {             // Count of active markets by category
        "sports": 3,
        "personal": 5,
        "academic": 2
    },
    "activity_heatmap": [ ... ],        // Trades per hour over last 7 days (168 data points)
    "sentiment_trend": [ ... ],         // Daily average optimism_score over last 30 days
    "honesty_index": 0.78,             // % of resolution votes that matched actual outcome
    "top_rivalries": [                  // Pairs of users who frequently oppose each other
        { "user_a": "...", "user_b": "...", "opposed_count": 8, "a_wins": 5 }
    ],
    "prophet_vs_humans": {              // Prophet's win rate vs average human win rate
        "prophet_accuracy": 0.68,
        "human_avg_accuracy": 0.55
    }
}
```

**Frontend Visualization Components**:
- **Optimism Gauge**: A radial gauge (like a speedometer) showing room optimism (green right, red left).
- **Topic Radar**: A radar/spider chart showing distribution of market categories.
- **Activity Heatmap**: A GitHub-contribution-style grid showing trading activity patterns.
- **Sentiment Trend Line**: A Recharts line chart of daily sentiment over time.
- **Rivalry Cards**: Pairs of user avatars with head-to-head records.
- **Honesty Meter**: A simple progress bar showing room's voting honesty.

### 7.4 Manipulation Detection

**Concept**: Prophet monitors trading and voting patterns and flags anomalies with playful commentary.

**Detection Rules** (implemented as checks after each trade and after each vote):

```python
# Rule 1: Large Last-Minute Bet
# Trigger: A single trade > 3x the market's average trade size AND placed within
# the final 10% of the market's lifetime (e.g., last 2.4 hours of a 24-hour market)
def check_large_last_minute(trade, market, all_trades):
    avg_trade = sum(t.amount for t in all_trades) / len(all_trades) if all_trades else 0
    time_remaining_pct = (market.expires_at - trade.created_at) / (market.expires_at - market.created_at)
    if trade.amount > avg_trade * 3 and time_remaining_pct < 0.1:
        return AnomalyFlag(
            flag_type='large_last_minute_bet',
            severity='medium',
            description=f"🚨 {trade.user.display_name} just dropped {trade.amount} coins on "
                        f"{'YES' if trade.side == 'yes' else 'NO'} with {minutes_left} minutes left. "
                        f"Prophet smells insider info."
        )

# Rule 2: Coordinated Same-Direction Bets
# Trigger: 3+ users place bets on the same side within a 60-second window
def check_coordinated_bets(trade, market, recent_trades_60s):
    same_side = [t for t in recent_trades_60s if t.side == trade.side and t.user_id != trade.user_id]
    if len(same_side) >= 2:  # 3 total including current trade
        return AnomalyFlag(
            flag_type='coordinated_same_direction',
            severity='medium',
            description=f"👀 {len(same_side)+1} people just piled onto {'YES' if trade.side == 'yes' else 'NO'} "
                        f"within a minute. Coincidence? Prophet thinks not."
        )

# Rule 3: Sudden Reversal
# Trigger: odds_yes swings more than 0.25 (25 percentage points) within 5 minutes
def check_sudden_reversal(market, odds_5min_ago):
    if abs(market.odds_yes - odds_5min_ago) > 0.25:
        return AnomalyFlag(
            flag_type='sudden_reversal',
            severity='high',
            description=f"📈📉 Market '{market.title}' just swung {abs(market.odds_yes - odds_5min_ago)*100:.0f} points "
                        f"in 5 minutes. Someone knows something."
        )

# Rule 4: Volume Spike
# Trigger: Trade volume in last hour > 5x the market's average hourly volume
def check_volume_spike(market, trades_last_hour, avg_hourly_volume):
    current_volume = sum(t.amount for t in trades_last_hour)
    if avg_hourly_volume > 0 and current_volume > avg_hourly_volume * 5:
        return AnomalyFlag(
            flag_type='volume_spike',
            severity='low',
            description=f"🔥 Trading volume on '{market.title}' is 5x normal. Something's brewing."
        )

# Rule 5: Vote Collusion (checked during resolution)
# Trigger: All users who bet on the same side also voted the same way AND that side lost
def check_vote_collusion(market, votes, trades):
    # Group voters by their trading position
    for side in ['yes', 'no']:
        traders_on_side = {t.user_id for t in trades if t.side == side}
        voters_on_side = {v.user_id for v in votes if v.vote == side}
        overlap = traders_on_side & voters_on_side
        if len(overlap) >= 3 and overlap == traders_on_side:
            return AnomalyFlag(
                flag_type='vote_collusion',
                severity='high',
                description=f"🤔 Interesting... every single person who bet {'YES' if side == 'yes' else 'NO'} "
                            f"also voted {'YES' if side == 'yes' else 'NO'}. Prophet is watching."
            )
```

**After detecting anomalies**: Insert into `anomaly_flags` table AND create a `narrative_event` with `event_type = 'manipulation_alert'`. The event appears in the room feed.

### 7.5 Hedge Mode

**Concept**: Prophet analyzes a user's open positions across all active markets in a room and suggests counter-bets to reduce risk.

**Endpoint**: `GET /api/users/:id/hedge-suggestions?room_id=...`

**Algorithm**:

```python
def generate_hedge_suggestions(user_id, room_id):
    # 1. Get all user's open positions in active markets in this room
    positions = get_open_positions(user_id, room_id)

    # 2. Calculate net exposure
    total_yes_exposure = sum(p.shares * p.odds_at_trade for p in positions if p.side == 'yes')
    total_no_exposure = sum(p.shares * p.odds_at_trade for p in positions if p.side == 'no')
    net_direction = 'bullish' if total_yes_exposure > total_no_exposure else 'bearish'
    imbalance = abs(total_yes_exposure - total_no_exposure)

    # 3. Find markets where a counter-bet would reduce exposure
    suggestions = []
    for market in get_active_markets(room_id):
        user_position = get_user_position(user_id, market.id)
        if user_position is None:
            # User has no position — suggest if it would balance portfolio
            suggested_side = 'no' if net_direction == 'bullish' else 'yes'
            suggested_amount = min(imbalance * 0.2, user_balance * 0.1)  # Conservative
            suggestions.append({
                'market_id': market.id,
                'market_title': market.title,
                'suggested_side': suggested_side,
                'suggested_amount': round(suggested_amount, 2),
                'reasoning': f"You're heavy on {'YES' if net_direction == 'bullish' else 'NO'} bets overall. "
                             f"A {suggested_side.upper()} bet here would balance your exposure."
            })

    # 4. Have Prophet generate a natural-language summary
    summary = call_prophet_commentary(positions, suggestions)

    return {
        'net_direction': net_direction,
        'imbalance': imbalance,
        'total_positions': len(positions),
        'suggestions': suggestions[:3],  # Top 3 suggestions
        'prophet_summary': summary
    }
```

**UI**: Display as a card on the user's profile page titled "Prophet's Hedge Advice" with the summary and clickable suggestion cards that pre-fill the trade form.

### 7.6 Live Odds Ticker

**Concept**: A persistent horizontal scrolling banner at the top of the Home Feed showing real-time odds movements.

**Frontend Implementation**:

```
┌────────────────────────────────────────────────────────────────────┐
│ 🔴 Will Jake pass calc? 62% ▲3  |  🟢 Snow tomorrow? 41% ▼7  |  │
│ 🔥 Prof curves final? 78% ▲12  |  🆕 New: Pizza or sushi?     │
└────────────────────────────────────────────────────────────────────┘
```

**Data Source**: WebSocket subscription on `/ws/ticker/:room_id`. Backend pushes events whenever `markets.odds_yes` changes.

**Ticker Item Schema**:

```json
{
    "market_id": "uuid",
    "title": "Will Jake pass calc?",       // Truncated to 30 chars
    "odds_yes": 0.62,
    "change_1h": 0.03,                     // Change in last hour (+/-)
    "volume_1h": 450,                      // Coins traded in last hour
    "is_hot": true,                        // Volume > 2x average
    "is_new": false,                       // Created in last 2 hours
    "status": "active"
}
```

**Visual Rules**:
- Green up arrow (▲) if `change_1h > 0`, red down arrow (▼) if negative
- 🔥 emoji prefix if `is_hot = true`
- 🆕 emoji prefix if `is_new = true`
- Clicking any ticker item navigates to market detail
- Auto-scrolls continuously with CSS animation, pauses on hover
- "Breaking" flash animation (background pulse) when a market swings > 15% in an hour

### 7.7 Market Derivatives / Options

**Concept**: Meta-markets that bet on the behavior of other markets, not on real-world outcomes.

**Types of Derivatives**:

| Type | Example | Auto-Resolution |
|---|---|---|
| Odds Threshold | "Will 'Jake passes calc' hit 80% YES before Friday?" | Check `reference_market.odds_yes >= threshold` before `threshold_deadline` |
| Volume Threshold | "Will 'Snow tomorrow' get 20+ trades?" | Check `COUNT(trades) >= threshold` for reference market |
| Resolution Bet | "Will 'Prof curves final' resolve via Prophet dispute?" | Check `reference_market.resolution_method == 'prophet'` |

**Creation Flow**:
1. User navigates to a market detail page.
2. Clicks "Create Derivative" button.
3. Selects derivative type and sets parameters (threshold value, deadline).
4. System creates a new market with `market_type = 'derivative'`, `reference_market_id` set, `threshold_condition` stored as a JSON string.
5. Prophet auto-generates a title: "Will '{reference_market.title}' hit {threshold}% before {deadline}?"

**Auto-Resolution**:
Derivative markets are checked by a background Celery task running every 60 seconds:

```python
# Celery periodic task: check_derivative_conditions
def check_derivative_conditions():
    active_derivatives = Market.query.filter_by(market_type='derivative', status='active').all()
    for deriv in active_derivatives:
        ref_market = Market.query.get(deriv.reference_market_id)
        condition = json.loads(deriv.threshold_condition)

        resolved = False
        result = None

        if condition['type'] == 'odds_threshold':
            if ref_market.odds_yes >= condition['value']:
                resolved, result = True, 'yes'
            elif datetime.now() >= deriv.threshold_deadline:
                resolved, result = True, 'no'

        elif condition['type'] == 'volume_threshold':
            trade_count = Trade.query.filter_by(market_id=ref_market.id).count()
            if trade_count >= condition['value']:
                resolved, result = True, 'yes'
            elif datetime.now() >= deriv.threshold_deadline:
                resolved, result = True, 'no'

        elif condition['type'] == 'resolution_method':
            if ref_market.status == 'resolved':
                result = 'yes' if ref_market.resolution_method == condition['value'] else 'no'
                resolved = True

        if resolved:
            resolve_market(deriv, result, method='automatic')
```

**Prophet Auto-Generation**: When a market becomes "hot" (volume > 3x average), the Market Gen Agent should consider creating 1-2 derivative markets automatically.

### 7.8 Spectator Mode

**Concept**: Users can join rooms as spectators — they see everything but cannot bet or vote.

**Implementation Details**:

- **Joining**: When joining a room, user selects role. Default is `participant`. Spectators click "Watch" instead of "Join."
- **Permissions**:
  - ✅ View all markets, trades, feed, leaderboard, Vibe Check
  - ✅ React with emoji on markets (reactions feed into Vibe Check sentiment)
  - ✅ View Prophet commentary and narrative arcs
  - ❌ Cannot place trades
  - ❌ Cannot cast resolution votes
  - ❌ Cannot create markets or submit whispers
  - ❌ In cash rooms: cannot see exact dollar amounts (only percentages and relative positions)
- **UI Differences**:
  - Trade buttons show "Join as Bettor to Trade" CTA
  - Vote buttons show "Participants Only"
  - Spectator badge next to name in member list
  - Spectator count displayed on room card: "12 bettors · 5 watching"
- **Upgrade**: Spectators can upgrade to participant at any time. They receive the default starting coins for that room.
- **Value**: Spectators boost room social proof and provide reaction data. They may convert to participants after watching the action.

---

## 8. Clout Score System (ELO)

### 8.1 ELO Calculation

After each market resolves, update each participant's Clout Score using an ELO-inspired system:

```python
K = 32  # ELO K-factor (how much each market moves your score)

def update_clout(user, market, user_won: bool):
    """
    user_won: True if user's net position was on the winning side.
    Uses the market's odds at time of user's trade as the "expected" probability.
    """
    # Expected score: the probability that the user's side would win
    # Based on the odds at time of their trade
    user_trades = get_user_trades(user.id, market.id)
    avg_odds = sum(t.odds_at_trade for t in user_trades) / len(user_trades)

    if user_trades[0].side == 'yes':
        expected = avg_odds
    else:
        expected = 1.0 - avg_odds

    actual = 1.0 if user_won else 0.0

    # ELO update
    user.clout_score += K * (actual - expected)

    # Clamp to minimum 0
    user.clout_score = max(0, user.clout_score)

    # Update rank label
    user.clout_rank = get_rank_label(user.clout_score)
```

### 8.2 Rank Labels

| Score Range | Rank |
|---|---|
| 0 - 800 | Bronze |
| 800 - 1000 | Silver |
| 1000 - 1200 | Gold |
| 1200 - 1400 | Platinum |
| 1400 - 1600 | Diamond |
| 1600+ | Prophet's Rival |

### 8.3 Prophet's Clout Score

Prophet starts at 1000 and is updated the same way as users. This creates a trackable AI-vs-human narrative. Display Prophet's rank on the room leaderboard alongside users.

---

## 9. AI Agent System (Prophet)

### 9.1 Architecture

Prophet consists of 4 specialized agents orchestrated via LangGraph. Each agent is a Claude API call with specific system prompts and tools.

```
                    ┌─────────────────┐
                    │   Orchestrator   │
                    │   (LangGraph)    │
                    └───────┬─────────┘
            ┌───────┬───────┼───────┬────────┐
            ▼       ▼       ▼       ▼        ▼
      ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
      │Market│ │ Odds │ │Resol.│ │Comms │
      │ Gen  │ │Engine│ │Agent │ │Agent │
      └──────┘ └──────┘ └──────┘ └──────┘
```

### 9.2 Market Generation Agent

**Trigger**: Runs periodically (every 4-6 hours per room) and on-demand when room activity spikes.

**System Prompt**:
```
You are Prophet, the AI market maker for a social prediction market room called "{room_name}".
Your job is to generate interesting, fun, engaging prediction markets based on the room's
recent activity, current events, and the interests of room members.

Guidelines:
- Markets should be resolvable (clear yes/no outcome) within 1-7 days
- Mix categories: personal bets, sports, pop culture, academic, weather, etc.
- Reference specific room members by name when appropriate for personal markets
- Consider generating conditional chains (if-then markets) when logical
- Consider generating derivatives on high-activity existing markets
- Keep titles concise (under 80 characters) but specific
- Be playful, provocative, and occasionally spicy — but never mean-spirited or harmful
- Generate 2-5 markets per batch

Room members: {member_list}
Recent markets: {recent_markets}
Recent narrative events: {recent_events}
Current trending topics: {trending_topics from web search}
```

**Output Schema**:
```json
{
    "markets": [
        {
            "title": "string",
            "description": "string | null",
            "category": "sports | personal | academic | politics | entertainment | weather | other",
            "initial_odds_yes": 0.5,
            "expires_in_hours": 48,
            "market_type": "standard | chained",
            "children": [
                {
                    "title": "string",
                    "trigger_condition": "parent_resolves_yes | parent_resolves_no",
                    "initial_odds_yes": 0.5,
                    "expires_in_hours": 48
                }
            ]
        }
    ]
}
```

**Tools Available**: `web_search` (for trending topics, sports schedules, weather forecasts).

### 9.3 Odds / Pricing Agent

**Role**: Sets initial odds on Prophet-generated markets and places Prophet's own bets.

**For initial odds**: Uses web search + room context to set a reasonable starting probability. For personal markets ("Will Jake go to the gym?"), defaults closer to 0.5. For verifiable events ("Will it rain tomorrow?"), uses data to set informed odds.

**For Prophet's bets**: After a market is created, this agent decides Prophet's position:

```json
{
    "side": "yes | no",
    "confidence": 0.0-1.0,
    "amount": 50-200,           // Virtual coins
    "reasoning": "string"        // Public explanation
}
```

### 9.4 Resolution Agent

**Trigger**: Called when a market enters `disputed` status (no 3/4 supermajority).

**System Prompt**:
```
You are Prophet, the impartial judge for disputed prediction markets.
A market has failed to reach a 3/4 supermajority in community voting.
You must review the evidence and make a binding ruling.

Market: {title}
Description: {description}
Vote distribution: {yes_votes} YES, {no_votes} NO
Trade distribution: {yes_traders} people bet YES, {no_traders} people bet NO
Room context: {recent room activity}

Rules:
- Search the web for objective evidence if the market is about a verifiable event
- Consider the market title carefully — what exactly was being predicted?
- Your ruling is final and must be either YES or NO
- Provide 2-4 sentences of reasoning that will be shown to all room members
- Be fair but also entertaining in your reasoning
```

**Tools Available**: `web_search`

**Output Schema**:
```json
{
    "ruling": "yes | no",
    "confidence": 0.0-1.0,
    "reasoning": "string",
    "evidence_sources": ["url1", "url2"]
}
```

### 9.5 Commentary Agent

**Trigger**: Called after trades, after resolutions, on anomaly detection, periodically for narrative arcs, and weekly for recaps.

**Commentary Types and Triggers**:

| Type | Trigger | Example Output |
|---|---|---|
| Trade Commentary | Major trade (> 2x avg) | "Alex just went all-in on YES. Bold move considering they're 2-8 on sports markets." |
| Resolution Recap | After market resolves | "The gym market resolves YES. Jake actually went. Prophet didn't see that coming." |
| Manipulation Alert | Anomaly detected | "🚨 3 people just piled onto NO within 30 seconds. Prophet is watching." |
| Narrative Arc | Periodic (daily) | "Jake's Redemption Arc, Chapter 3: After 7 straight losses..." |
| Rivalry Update | After resolution where rivals are on opposite sides | "Sarah vs Mike: Round 13. Sarah takes this one, leading 9-4." |
| Weekly Recap | Sunday midnight | "This week in {room_name}: 12 markets resolved, biggest upset was..." |
| Prophet Challenge | When a user is on a streak | "Hey @Alex, you've called 5 in a row. Prophet challenges you: bet on {market}." |
| Achievement Alert | Badge earned | "🏆 @Sarah just earned 'Oracle' — 5 correct predictions in a row!" |

**System Prompt**:
```
You are Prophet, the AI personality of a social prediction market room.
You generate entertaining commentary about betting activity, user behavior, and market outcomes.
Your tone is: witty, slightly roast-y, always playful, never genuinely mean.
Think sports commentator meets group chat instigator.
Keep all commentary to 1-3 sentences maximum.
Reference specific users by name. Use inside jokes from room history when possible.
Use emojis sparingly but effectively.
```

### 9.6 Agent Orchestration (LangGraph)

The LangGraph graph defines the flow:

```python
from langgraph.graph import StateGraph, END

# State shared across agents
class ProphetState(TypedDict):
    room_id: str
    trigger: str  # 'trade', 'resolution', 'periodic', 'anomaly'
    context: dict  # Relevant data for the triggered event
    markets_to_create: list
    bets_to_place: list
    commentary_to_post: list
    anomalies_detected: list

def market_gen_node(state):
    # Call Market Gen Agent, return updated state with markets_to_create
    ...

def odds_node(state):
    # Set odds and place Prophet bets on new markets
    ...

def resolution_node(state):
    # Handle disputed market resolution
    ...

def commentary_node(state):
    # Generate and post commentary
    ...

def anomaly_node(state):
    # Check for manipulation patterns
    ...

# Build graph
graph = StateGraph(ProphetState)
graph.add_node("anomaly_check", anomaly_node)
graph.add_node("commentary", commentary_node)
graph.add_node("market_gen", market_gen_node)
graph.add_node("odds", odds_node)
graph.add_node("resolution", resolution_node)

# Routing based on trigger
def route(state):
    if state['trigger'] == 'trade':
        return 'anomaly_check'
    elif state['trigger'] == 'resolution_dispute':
        return 'resolution'
    elif state['trigger'] == 'periodic':
        return 'market_gen'
    else:
        return 'commentary'

graph.set_conditional_entry_point(route)
graph.add_edge("anomaly_check", "commentary")  # Always comment after checking
graph.add_edge("market_gen", "odds")            # Set odds after generating
graph.add_edge("odds", "commentary")            # Comment on new markets
graph.add_edge("resolution", "commentary")      # Comment on resolution
graph.add_edge("commentary", END)

prophet = graph.compile()
```

---

## 10. Frontend — Pages and Components

### 10.1 Page Map

```
/                       → Landing page (unauthenticated)
/home                   → Home Feed (authenticated)
/room/:id               → Room View
/room/:id/vibe          → Vibe Check Dashboard
/room/:id/leaderboard   → Room Leaderboard
/market/:id             → Market Detail
/market/:id/chain       → Chain Visualization
/profile/:id            → User Profile
/profile/:id/hedge      → Hedge Mode Suggestions
/settings               → Account settings
```

### 10.2 Landing Page (`/`)

**Purpose**: Convert visitors into users.

**Layout**:
- Hero section: Large animated title "PROPHECY", subtitle "Bet on anything with your friends. Prophet keeps score."
- Three-feature showcase with animated cards (Rooms, Prophet AI, Real Money)
- "Create a Room in 10 Seconds" CTA button → triggers Google OAuth
- Live stats ticker at bottom: "X markets active · Y bets placed today · Z rooms"
- Dark theme with subtle particle/smoke background animation (Framer Motion)

### 10.3 Home Feed (`/home`)

**Purpose**: Central hub showing activity across all user's rooms.

**Layout**:
```
┌─────────────────────────────────────────────┐
│  LIVE ODDS TICKER (horizontal scrolling)    │  ← Section 7.6
├─────────────────────────────────────────────┤
│  Room Selector Tabs: [All] [Room1] [Room2]  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Market Card (active)                │    │
│  │ "Will it snow tomorrow?"            │    │
│  │ YES 62% ████████░░ NO 38%           │    │
│  │ 💰 450 coins · 12 trades · ⏰ 8h    │    │
│  │ [Bet YES] [Bet NO]                  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Narrative Card (Prophet commentary) │    │
│  │ 🤖 Prophet: "Jake's Redemption      │    │
│  │ Arc continues..."                   │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Market Card (voting phase)          │    │
│  │ "Did Jake go to the gym?"           │    │
│  │ 🗳️ VOTING · 8/12 voted · ⏰ 16h     │    │
│  │ [Vote YES] [Vote NO]               │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  ... (infinite scroll, paginated)           │
└─────────────────────────────────────────────┘
```

**Feed Ordering**: Interleave markets and narrative events, sorted by `created_at DESC`. Pinned items: markets in `voting` status always appear at top.

### 10.4 Room View (`/room/:id`)

**Tabs**: Markets | Feed | Leaderboard | Vibe Check | Members | Settings (admin)

**Markets Tab**: Grid/list of active markets in this room, filterable by category and status. "Create Market" and "Whisper a Market" buttons at top.

**Feed Tab**: Same as Home Feed but filtered to this room only.

**Leaderboard Tab**: Ranked list of members by clout_score. Shows: rank, avatar, name, clout score, rank label, win rate, current streak. Prophet appears in the list with its own entry.

**Members Tab**: List of participants and spectators with roles. Admin can change roles.

### 10.5 Market Detail (`/market/:id`)

**Layout**:
```
┌─────────────────────────────────────────────┐
│  Market Title                               │
│  "Will Professor Kim curve the final?"       │
│  Created by @Sarah · Category: Academic      │
│  Status: ACTIVE · Expires: Feb 18, 8:00 PM  │
├─────────────────────────────────────────────┤
│  ODDS CHART (Recharts line chart)           │
│  Shows odds_yes over time with trade markers│
│  ┌───────────────────────────────────┐      │
│  │    78% ─────────╱──── current     │      │
│  │   /            ╱                  │      │
│  │  50%──────────╱                   │      │
│  │  ▲ Feb 14    ▲ Feb 15   ▲ Feb 16 │      │
│  └───────────────────────────────────┘      │
├─────────────────────────────────────────────┤
│  TRADE PANEL                                │
│  Current: YES 78% / NO 22%                  │
│  Prophet says: YES (72% confidence)         │
│  Amount: [____] coins                       │
│  [BET YES] [BET NO]                         │
│  Est. payout if correct: X coins            │
├─────────────────────────────────────────────┤
│  WHO'S BETTING                              │
│  YES side: @Jake, @Sarah, 🤖Prophet (+3)    │
│  NO side: @Mike, @Alex (+1)                 │
├─────────────────────────────────────────────┤
│  TRADE HISTORY                              │
│  @Jake bought YES for 50 coins (at 62%)     │
│  @Mike bought NO for 30 coins (at 65%)      │
│  ...                                        │
├─────────────────────────────────────────────┤
│  CHAIN VIEW (if chained market)             │
│  Shows parent/child tree (see Section 7.1)  │
├─────────────────────────────────────────────┤
│  DERIVATIVES (if any exist)                 │
│  "Will this market hit 90%?" → 45% YES      │
│  [Create Derivative]                        │
└─────────────────────────────────────────────┘
```

**During Voting Phase**: Replace trade panel with:
```
┌─────────────────────────────────────────────┐
│  🗳️ RESOLUTION VOTING                       │
│  Did this event actually happen?             │
│  Votes: 8/12 members voted                  │
│  (Individual votes hidden until deadline)    │
│  Deadline: Feb 19, 8:00 PM                  │
│  [VOTE YES] [VOTE NO]                       │
│  (You voted: YES ✓) ← shown after voting    │
│  Requires 3/4 supermajority to resolve      │
└─────────────────────────────────────────────┘
```

**After Resolution**: Show results, payouts, Prophet's commentary, vote breakdown.

### 10.6 User Profile (`/profile/:id`)

```
┌─────────────────────────────────────────────┐
│  @JakeMiller                                │
│  🏆 Clout: 1247 (Platinum)                  │
│  Record: 34W - 21L (62%) · Streak: 3 🔥     │
├─────────────────────────────────────────────┤
│  BADGES                                     │
│  🔮 Oracle · 👑 Upset King · 💎 Diamond Hands│
├─────────────────────────────────────────────┤
│  OPEN POSITIONS                             │
│  "Snow tomorrow" → YES @ 62% · 50 coins     │
│  "Jake passes calc" → NO @ 45% · 30 coins   │
├─────────────────────────────────────────────┤
│  PROPHET'S HEDGE ADVICE                     │
│  "You're heavy on YES bets this week..."     │
│  [Suggested: Bet NO on 'Prof curves final']  │
├─────────────────────────────────────────────┤
│  RECENT ACTIVITY                            │
│  Bet YES on "Snow tomorrow" · 2h ago        │
│  Won "Chiefs win" · +120 coins · yesterday   │
└─────────────────────────────────────────────┘
```

### 10.7 Shared Component Library

Build these as reusable React components:

| Component | Props | Used In |
|---|---|---|
| `<MarketCard>` | market, onBet, compact? | Feed, Room View |
| `<NarrativeCard>` | event | Feed |
| `<OddsBar>` | oddsYes, animated? | Market Card, Detail |
| `<OddsChart>` | tradeHistory[] | Market Detail |
| `<TradePanel>` | market, userBalance, onTrade | Market Detail |
| `<VotePanel>` | market, userVote, voteCount, onVote | Market Detail (voting) |
| `<LeaderboardRow>` | user, rank | Leaderboard |
| `<BadgeDisplay>` | badges[] | Profile |
| `<LiveTicker>` | tickerItems[] | Home Feed top |
| `<ChainTree>` | rootMarket, children[] | Market Detail, Chain View |
| `<VibeGauge>` | score, label | Vibe Check |
| `<HedgeCard>` | suggestion | Profile |
| `<AnomalyAlert>` | flag | Feed |
| `<WhisperForm>` | roomId, onSubmit | Room View |
| `<SpectatorBanner>` | onUpgrade | Room View (spectators) |
| `<UserAvatar>` | user, size | Everywhere |
| `<RoomCard>` | room, memberCount, spectatorCount | Home sidebar |
| `<DerivativeLink>` | derivative, parentMarket | Market Detail |

---

## 11. Background Tasks (Celery)

### 11.1 Periodic Tasks

| Task | Schedule | Description |
|---|---|---|
| `check_market_expiry` | Every 60 seconds | Find markets past `expires_at` still in `active` → move to `voting`, set `voting_deadline` |
| `check_voting_deadline` | Every 60 seconds | Find markets past `voting_deadline` → tally votes, resolve or dispute |
| `check_derivative_conditions` | Every 60 seconds | Check active derivatives for threshold met → auto-resolve |
| `trigger_chained_markets` | On market resolution | Activate pending child markets whose trigger condition is met |
| `prophet_market_generation` | Every 4-6 hours per room | Run Market Gen Agent for each active room |
| `prophet_narrative_arcs` | Daily at midnight | Run Commentary Agent for daily narrative updates per room |
| `prophet_weekly_recap` | Sunday midnight | Generate weekly recap per room |
| `update_clout_scores` | On market resolution | Recalculate ELO for all participants in resolved market |
| `check_achievements` | On market resolution | Check and award new badges |
| `virtual_coin_airdrop` | Weekly (Monday) | Give all participants in virtual rooms 200 bonus coins |
| `clout_decay` | Daily | Reduce inactive users' clout by 0.5% per day of inactivity (min 7 days idle) |
| `cleanup_expired_whispers` | Daily | Delete rejected/expired whispers older than 30 days |

### 11.2 Event-Driven Tasks

| Trigger | Task |
|---|---|
| Trade placed | `run_anomaly_detection(trade_id)` |
| Market resolved | `distribute_payouts(market_id)`, `trigger_chained_markets(market_id)`, `update_clout_scores(market_id)`, `check_achievements(market_id)`, `prophet_resolution_commentary(market_id)` |
| Market disputed | `prophet_dispute_resolution(market_id)` |
| Market becomes hot | `prophet_generate_derivatives(market_id)` |
| User joins room | `prophet_welcome_message(user_id, room_id)` |
| Resolution votes cast | `check_vote_collusion(market_id)` after each vote |

---

## 12. Demo Strategy (Hackathon Presentation)

### 12.1 Pre-Seeded Data

Before the demo, pre-populate the database with:
- 1 room called "Columbia Hackathon 2025" with 8-10 fake users
- 15-20 markets in various states (active, voting, resolved)
- 50+ trades creating realistic odds movement
- 5-6 narrative events from Prophet
- 2 anomaly flags
- 1 chained market tree (3 levels)
- 1 derivative market
- 2 whisper markets
- A complete leaderboard with varied clout scores and badges

### 12.2 Live Demo Script (5 minutes)

1. **Open landing page** (15 seconds) — Show the polished hero, animated background.
2. **Log in, show Home Feed** (30 seconds) — Scroll through the feed, point out the live ticker, narrative cards, different market states.
3. **Enter room, show leaderboard** (20 seconds) — Point out Prophet's entry with its own clout score.
4. **Show Vibe Check dashboard** (20 seconds) — Animated gauges, rivalry cards, topic radar.
5. **Create a market live** (30 seconds) — "Will a judge ask a question about monetization?" Show it appear in the feed.
6. **Show Prophet auto-generating a market** (20 seconds) — Trigger the Market Gen Agent, show a new market appear with Prophet's reasoning.
7. **Invite a judge to join** (30 seconds) — Share join code, judge joins as spectator, show spectator count update.
8. **Judge upgrades to participant, places a bet** (30 seconds) — Watch odds shift in real-time on the ticker.
9. **Show a chained market tree** (20 seconds) — Visual chain view, explain conditional activation.
10. **Show a derivative market** (15 seconds) — "This is a bet on the odds of another bet."
11. **Trigger a resolution vote** (30 seconds) — Show the voting UI, hidden votes, explain the 3/4 supermajority and how it turns resolution into a game.
12. **Show a Prophet dispute resolution** (20 seconds) — Pre-resolved disputed market with Prophet's reasoning visible.
13. **Show manipulation detection** (15 seconds) — Anomaly alert card in the feed.
14. **Flash the Hedge Mode suggestion** (15 seconds) — Show Prophet's portfolio advice on a profile.
15. **Explain real money architecture** (30 seconds) — Show the cash room toggle, explain Privy + USDC, show Base testnet transaction.
16. **Close with the pitch** (15 seconds) — "Prophecy: where your opinions have consequences."

Total: ~5 minutes

### 12.3 Backup Plan

If live features break during demo, have screenshots/recordings of each feature as fallback slides. Record a smooth run-through the night before.

---

## 13. File Structure

```
prophecy/
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── market/
│   │   │   │   ├── MarketCard.jsx
│   │   │   │   ├── OddsBar.jsx
│   │   │   │   ├── OddsChart.jsx
│   │   │   │   ├── TradePanel.jsx
│   │   │   │   ├── VotePanel.jsx
│   │   │   │   ├── ChainTree.jsx
│   │   │   │   └── DerivativeLink.jsx
│   │   │   ├── feed/
│   │   │   │   ├── NarrativeCard.jsx
│   │   │   │   ├── AnomalyAlert.jsx
│   │   │   │   └── LiveTicker.jsx
│   │   │   ├── room/
│   │   │   │   ├── RoomCard.jsx
│   │   │   │   ├── LeaderboardRow.jsx
│   │   │   │   ├── WhisperForm.jsx
│   │   │   │   └── SpectatorBanner.jsx
│   │   │   ├── profile/
│   │   │   │   ├── BadgeDisplay.jsx
│   │   │   │   └── HedgeCard.jsx
│   │   │   ├── vibe/
│   │   │   │   ├── VibeGauge.jsx
│   │   │   │   ├── TopicRadar.jsx
│   │   │   │   ├── ActivityHeatmap.jsx
│   │   │   │   └── RivalryCard.jsx
│   │   │   └── shared/
│   │   │       ├── UserAvatar.jsx
│   │   │       ├── Button.jsx
│   │   │       ├── Modal.jsx
│   │   │       └── Layout.jsx
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── HomeFeed.jsx
│   │   │   ├── RoomView.jsx
│   │   │   ├── MarketDetail.jsx
│   │   │   ├── ChainView.jsx
│   │   │   ├── VibeCheck.jsx
│   │   │   ├── Profile.jsx
│   │   │   └── Settings.jsx
│   │   ├── hooks/
│   │   │   ├── useSupabaseRealtime.js
│   │   │   ├── useWebSocket.js
│   │   │   ├── useAuth.js
│   │   │   └── useMarket.js
│   │   ├── store/
│   │   │   ├── authStore.js
│   │   │   ├── roomStore.js
│   │   │   ├── marketStore.js
│   │   │   └── tickerStore.js
│   │   ├── lib/
│   │   │   ├── supabase.js
│   │   │   ├── api.js
│   │   │   └── privy.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, startup
│   │   ├── config.py                # Environment variables
│   │   ├── database.py              # Supabase/SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── room.py
│   │   │   ├── market.py
│   │   │   ├── trade.py
│   │   │   ├── vote.py
│   │   │   ├── whisper.py
│   │   │   ├── narrative.py
│   │   │   ├── anomaly.py
│   │   │   ├── payment.py
│   │   │   └── achievement.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── rooms.py
│   │   │   ├── markets.py
│   │   │   ├── trades.py
│   │   │   ├── votes.py
│   │   │   ├── whispers.py
│   │   │   ├── payments.py
│   │   │   └── websockets.py
│   │   ├── services/
│   │   │   ├── lmsr.py              # LMSR market maker (Section 5)
│   │   │   ├── resolution.py        # Resolution logic (Section 6)
│   │   │   ├── clout.py             # ELO calculation (Section 8)
│   │   │   ├── anomaly.py           # Manipulation detection (Section 7.4)
│   │   │   ├── hedge.py             # Hedge suggestions (Section 7.5)
│   │   │   ├── derivatives.py       # Derivative checking (Section 7.7)
│   │   │   ├── chains.py            # Chain activation (Section 7.1)
│   │   │   └── achievements.py      # Badge checks (Section 3.2)
│   │   ├── agents/
│   │   │   ├── orchestrator.py      # LangGraph graph definition (Section 9.6)
│   │   │   ├── market_gen.py        # Market Generation Agent (Section 9.2)
│   │   │   ├── odds.py              # Odds/Pricing Agent (Section 9.3)
│   │   │   ├── resolution.py        # Resolution Agent (Section 9.4)
│   │   │   ├── commentary.py        # Commentary Agent (Section 9.5)
│   │   │   └── prompts.py           # All system prompts centralized
│   │   └── tasks/
│   │       ├── celery_app.py        # Celery configuration
│   │       ├── periodic.py          # Periodic tasks (Section 11.1)
│   │       └── event_driven.py      # Event-driven tasks (Section 11.2)
│   ├── requirements.txt
│   └── Dockerfile
│
├── database/
│   └── schema.sql                   # Complete schema (Section 3)
│
├── contracts/                       # (Optional) Solidity escrow contract
│   └── Escrow.sol
│
├── .env.example
├── docker-compose.yml               # Local dev: backend + Redis
└── README.md
```

---

## 14. Environment Variables

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbG...
SUPABASE_SERVICE_KEY=eyJhbG...   # Server-side only

# Auth
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx

# Anthropic (Claude API for Prophet)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Privy (Wallet)
PRIVY_APP_ID=xxxxx
PRIVY_APP_SECRET=xxxxx

# Redis
REDIS_URL=redis://localhost:6379

# Base Network (USDC)
BASE_RPC_URL=https://sepolia.base.org        # Testnet
USDC_CONTRACT_ADDRESS=0x...                   # Base Sepolia USDC
ESCROW_CONTRACT_ADDRESS=0x...                 # Deployed escrow

# App
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
SECRET_KEY=xxxxx                              # JWT signing
```

---

## 15. Implementation Priority Order

For a hackathon, build in this order. Each phase builds on the previous and produces a demoable state.

### Phase 1: Foundation (Hours 1-4)
1. Set up Supabase project, create all tables from Section 3
2. Set up FastAPI project with auth router (Google OAuth via Supabase)
3. Set up React project with Tailwind, routing, Supabase client
4. Build: Landing page, Google login, basic Home page shell
5. Implement: Create room, join room, room view with member list

### Phase 2: Core Trading (Hours 4-8)
6. Implement LMSR engine (`services/lmsr.py`)
7. Build: Create market API + UI
8. Build: Place trade API + UI (TradePanel component)
9. Build: MarketCard component with animated OddsBar
10. Build: Market Detail page with OddsChart
11. Wire up Supabase real-time for live odds updates

### Phase 3: Resolution (Hours 8-12)
12. Implement market expiry checker (Celery task)
13. Build: VotePanel component
14. Implement voting logic (3/4 supermajority)
15. Implement payout distribution
16. Implement Clout Score (ELO) updates
17. Build: Leaderboard page

### Phase 4: Prophet AI (Hours 12-18)
18. Build Market Gen Agent (Claude API call with web_search tool)
19. Build Odds Agent (initial odds + Prophet's own bet)
20. Build Resolution Agent (dispute handling)
21. Build Commentary Agent (post-trade, post-resolution commentary)
22. Wire up LangGraph orchestrator
23. Build NarrativeCard component, integrate into feed
24. Add Prophet to leaderboard with its own Clout Score

### Phase 5: Advanced Features (Hours 18-24)
25. Implement Chained Markets (parent_id, trigger, activation)
26. Build ChainTree visualization component
27. Implement Whisper Bets (submission, moderation, anonymous posting)
28. Implement Manipulation Detection (anomaly rules + alerts)
29. Implement Derivatives (creation, auto-resolution checker)
30. Implement Spectator Mode (role-based UI gating)

### Phase 6: Polish (Hours 24-30)
31. Build Live Odds Ticker component with WebSocket
32. Build Vibe Check Dashboard (gauges, charts, rivalry cards)
33. Implement Hedge Mode suggestions
34. Build achievement/badge system
35. Add Framer Motion animations to all cards and transitions
36. Build cash room UI (toggle, deposit/withdraw placeholders)
37. Pre-seed demo data
38. Polish landing page

### Phase 7: Demo Prep (Hours 30-36)
39. Record backup demo video
40. Test all features end-to-end
41. Prepare pitch script (Section 12.2)
42. Deploy frontend to Vercel, backend to Railway
43. Final database seed with compelling demo data

---

## 16. Design System

### 16.1 Color Palette

```css
/* Dark theme - primary */
--bg-primary: #0a0a0f;          /* Near-black background */
--bg-secondary: #12121a;        /* Card backgrounds */
--bg-tertiary: #1a1a2e;         /* Elevated surfaces */
--border: #2a2a3e;              /* Subtle borders */

/* Text */
--text-primary: #f0f0f5;        /* Primary text */
--text-secondary: #8888a0;      /* Secondary/muted text */
--text-accent: #b0b0c8;         /* Labels */

/* Accent - Prophet Purple */
--accent-primary: #8b5cf6;      /* Prophet purple */
--accent-hover: #7c3aed;
--accent-muted: #8b5cf620;      /* For backgrounds */

/* Trading */
--yes-green: #22c55e;           /* YES bets, positive movement */
--yes-green-muted: #22c55e20;
--no-red: #ef4444;              /* NO bets, negative movement */
--no-red-muted: #ef444420;

/* Status */
--active: #22c55e;
--voting: #f59e0b;
--disputed: #ef4444;
--resolved: #8888a0;

/* Special */
--prophet-glow: #8b5cf680;     /* Prophet avatar glow */
--hot-market: #f97316;          /* Hot/trending indicator */
--whisper: #6366f1;             /* Whisper market tint */
```

### 16.2 Typography

```css
/* Headings: Inter or Space Grotesk */
font-family: 'Space Grotesk', 'Inter', sans-serif;

/* Body: Inter */
font-family: 'Inter', sans-serif;

/* Monospace (odds, numbers): JetBrains Mono */
font-family: 'JetBrains Mono', monospace;
```

### 16.3 Card Styles

All cards should have:
- `bg-[#12121a]` background
- `border border-[#2a2a3e]` border
- `rounded-xl` border radius
- `p-4` padding
- Subtle hover: `hover:border-[#8b5cf640]` (prophet purple tint)
- Framer Motion: `whileHover={{ scale: 1.01 }}` subtle lift

### 16.4 Prophet's Visual Identity

Prophet should have a distinct visual presence:
- Avatar: A glowing purple eye/oracle icon
- Name always renders in accent purple with a subtle glow
- Prophet's commentary cards have a left border in accent purple
- Prophet's bets show a robot emoji (🤖) prefix
- In the leaderboard, Prophet's row has a subtle purple background tint

---

## 17. Error Handling and Edge Cases

### 17.1 Trading Edge Cases

- **Insufficient balance**: Return 400 with clear message, frontend disables bet button when balance < min_bet
- **Market not active**: Return 400 if market is in any state other than `active`
- **Self-trading**: Allowed (user can bet both YES and NO)
- **Zero-amount trade**: Reject, minimum is room's `min_bet`
- **Exceeds max_bet**: Reject, cap at room's `max_bet`
- **Concurrent trades**: Use database transactions with row-level locking on the market record to prevent race conditions in LMSR state updates

### 17.2 Resolution Edge Cases

- **No votes cast**: If zero votes by deadline, Prophet auto-resolves
- **All voters are on one side of the bet**: Flag as potential collusion but don't prevent resolution
- **Market creator votes**: Allowed, no special treatment
- **Spectator tries to vote**: API returns 403
- **User votes twice**: UNIQUE constraint prevents, API returns 409
- **Room has < 4 participants**: 3/4 supermajority still applies (e.g., 3 of 4 must agree)

### 17.3 Chain Edge Cases

- **Parent cancelled**: All pending children are also cancelled
- **Child market has no trades**: Skip payout, auto-cancel after expiry
- **Chain depth exceeded**: API rejects market creation if depth would exceed 3

### 17.4 Cash Room Edge Cases

- **Deposit not confirmed**: Don't credit balance until blockchain confirmation (6 blocks)
- **Withdrawal during active bets**: Only allow withdrawal of unlocked balance (total - amount in open positions)
- **Market cancelled in cash room**: Return all funds to traders

---

This specification is complete. An AI agent should be able to read this document and implement the entire Prophecy platform. Start with Phase 1 (Section 15) and build incrementally. Every API endpoint, database table, UI component, agent behavior, and background task is defined.
