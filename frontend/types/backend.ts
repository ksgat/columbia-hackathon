/**
 * Backend Types - Aligned with FastAPI Backend Models
 *
 * NOTE: Frontend previously used different terminology:
 * - Frontend "Market" = Backend "Room"
 * - Frontend "Prediction" = Backend "Market"
 * - Frontend "Bet" = Backend "Trade"
 */

// ============================================================================
// USER & AUTH
// ============================================================================

export interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  clout_score: number
  clout_rank: string
  total_bets_placed: number
  total_bets_won: number
  total_markets_created: number
  streak_current: number
  streak_best: number
  balance_virtual: number
  balance_cash: number
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// ============================================================================
// ROOMS (Frontend: "Markets")
// ============================================================================

export interface Room {
  id: string
  name: string
  description?: string
  join_code: string
  creator_id: string
  currency_mode: 'virtual' | 'cash' | 'both'
  min_bet: number
  max_bet: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Membership {
  id: string
  user_id: string
  room_id: string
  role: 'admin' | 'participant' | 'spectator'
  coins_virtual: number
  coins_cash: number
  coins_earned_total: number
  joined_at: string
}

export interface RoomMember {
  user_id: string
  display_name: string
  avatar_url?: string
  role: 'admin' | 'participant' | 'spectator'
  coins_virtual: number
  joined_at: string
}

// ============================================================================
// MARKETS (Frontend: "Predictions")
// ============================================================================

export type MarketType = 'standard' | 'chained' | 'derivative'
export type MarketStatus = 'pending' | 'active' | 'voting' | 'disputed' | 'resolved' | 'cancelled'

export interface Market {
  id: string
  room_id: string
  creator_id?: string // null for Prophet-generated
  title: string
  description?: string
  category?: string
  market_type: MarketType

  // LMSR Trading State
  odds_yes: number
  odds_no: number
  total_pool: number
  total_yes_shares: number
  total_no_shares: number
  lmsr_b: number

  // Status
  currency_mode: 'virtual' | 'cash'
  status: MarketStatus
  resolution_result?: 'yes' | 'no'
  resolution_method?: 'community' | 'prophet' | 'admin' | 'automatic'

  // Timestamps
  expires_at: string
  voting_deadline?: string
  resolved_at?: string
  created_at: string
  updated_at: string

  // Chained Markets
  parent_market_id?: string
  trigger_condition?: 'parent_resolves_yes' | 'parent_resolves_no'
  chain_depth?: number

  // Derivative Markets
  reference_market_id?: string
  threshold_condition?: string
  threshold_deadline?: string
}

// ============================================================================
// TRADING
// ============================================================================

export interface Trade {
  id: string
  market_id: string
  user_id?: string
  is_prophet_trade: boolean
  side: 'yes' | 'no'
  amount: number
  shares_received: number
  odds_at_trade: number
  currency: 'virtual' | 'cash'
  created_at: string
}

export interface Position {
  id: string
  user_id: string
  market_id: string
  side: 'yes' | 'no'
  total_shares: number
  avg_odds: number
  total_invested: number
  current_value: number
  unrealized_pnl: number
}

export interface TradeRequest {
  side: 'yes' | 'no'
  amount: number
}

export interface TradeResponse {
  trade_id: string
  shares_received: number
  new_odds_yes: number
  new_odds_no: number
  new_balance: number
}

// ============================================================================
// VOTING & RESOLUTION
// ============================================================================

export interface ResolutionVote {
  id: string
  market_id: string
  user_id: string
  vote: 'yes' | 'no'
  created_at: string
}

export interface VoteSummary {
  yes_votes: number
  no_votes: number
  total_votes: number
  user_vote?: 'yes' | 'no'
  votes: ResolutionVote[]
}

export interface ResolutionSummary {
  market_id: string
  result: 'yes' | 'no'
  method: string
  total_payout: number
  winners_count: number
  losers_count: number
  total_trades: number
  children_activated?: number
  activated_markets?: string[]
}

// ============================================================================
// PROPHET AI
// ============================================================================

export interface ProphetBet {
  id: string
  market_id: string
  side: 'yes' | 'no'
  confidence: number
  reasoning: string
  amount: number
  shares_received: number
  created_at: string
}

export interface ProphetStatus {
  status: 'online' | 'offline'
  model: string
  capabilities: string[]
}

export interface GeneratedMarket {
  title: string
  description?: string
  category?: string
  initial_odds_yes: number
}

export interface MarketGenerationResponse {
  message: string
  markets: GeneratedMarket[]
  commentary: string
}

// ============================================================================
// CHAINED MARKETS
// ============================================================================

export interface ChainTreeNode {
  market: Market
  children: ChainTreeNode[]
}

export interface CreateChainedMarketRequest {
  parent_market_id: string
  trigger_condition: 'parent_resolves_yes' | 'parent_resolves_no'
  title: string
  description?: string
  category?: string
  initial_odds_yes?: number
}

// ============================================================================
// DERIVATIVE MARKETS
// ============================================================================

export type DerivativeType = 'odds_threshold' | 'volume_threshold' | 'resolution_method'

export interface DerivativeStatus {
  derivative_id: string
  reference_market_id: string
  reference_market_title: string
  threshold_type: DerivativeType
  threshold_value: number | string
  deadline?: string
  current_odds?: number
  current_volume?: number
  reference_status?: string
  reference_resolution_method?: string
  progress_percent?: number
}

export interface CreateDerivativeRequest {
  reference_market_id: string
  threshold_type: DerivativeType
  threshold_value: string
  threshold_deadline?: string
  initial_odds_yes?: number
  auto_title?: boolean
  custom_title?: string
  description?: string
  category?: string
}

// ============================================================================
// CLOUT & RANKINGS
// ============================================================================

export interface UserStats {
  user_id: string
  display_name: string
  clout_score: number
  clout_rank: string
  total_bets_placed: number
  total_bets_won: number
  win_rate: number
  total_markets_created: number
  streak_current: number
  streak_best: number
  balance_virtual: number
  balance_cash: number
  total_profit: number
}

export const RANK_LABELS: Record<string, { min: number; label: string; color: string }> = {
  bronze: { min: 0, label: 'Bronze', color: '#CD7F32' },
  silver: { min: 800, label: 'Silver', color: '#C0C0C0' },
  gold: { min: 1000, label: 'Gold', color: '#FFD700' },
  platinum: { min: 1200, label: 'Platinum', color: '#E5E4E2' },
  diamond: { min: 1400, label: 'Diamond', color: '#B9F2FF' },
  prophets_rival: { min: 1600, label: "Prophet's Rival", color: '#9D00FF' },
}

// ============================================================================
// API RESPONSE WRAPPERS
// ============================================================================

export interface ApiError {
  detail: string
  status_code?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
