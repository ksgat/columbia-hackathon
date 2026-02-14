/**
 * API Client for Prophecy Backend
 *
 * Connects frontend to FastAPI backend running on localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// Helper function for API calls
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `API Error: ${response.statusText}`)
  }

  return response.json()
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(error.detail || 'Login failed')
  }

  const data = await response.json()

  // Store token
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  return data
}

export async function logout(): Promise<void> {
  await apiCall('/auth/logout', { method: 'POST' })

  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }
}

export async function getCurrentUser() {
  return apiCall('/auth/me', { method: 'GET' })
}

// ============================================================================
// ROOMS (what frontend calls "Markets")
// ============================================================================

export interface Room {
  id: string
  name: string
  description?: string
  join_code: string
  creator_id: string
  currency_mode: string
  is_active: boolean
  created_at: string
}

export interface CreateRoomRequest {
  name: string
  description?: string
}

export async function createRoom(data: CreateRoomRequest): Promise<Room> {
  return apiCall('/rooms', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getRooms(): Promise<Room[]> {
  return apiCall('/rooms', { method: 'GET' })
}

export async function getRoom(roomId: string): Promise<Room> {
  return apiCall(`/rooms/${roomId}`, { method: 'GET' })
}

export async function joinRoom(joinCode: string): Promise<any> {
  return apiCall('/rooms/join', {
    method: 'POST',
    body: JSON.stringify({ join_code: joinCode, role: 'participant' }),
  })
}

export async function getRoomMembers(roomId: string): Promise<any[]> {
  return apiCall(`/rooms/${roomId}/members`, { method: 'GET' })
}

// ============================================================================
// MARKETS (what frontend calls "Predictions")
// ============================================================================

export interface Market {
  id: string
  room_id: string
  creator_id?: string
  title: string
  description?: string
  category?: string
  market_type: string
  odds_yes: number
  odds_no: number
  total_pool: number
  total_yes_shares: number
  total_no_shares: number
  status: string
  expires_at: string
  created_at: string
  // Chained market fields
  parent_market_id?: string
  trigger_condition?: string
  chain_depth?: number
  // Derivative fields
  reference_market_id?: string
  threshold_condition?: string
  threshold_deadline?: string
}

export interface CreateMarketRequest {
  room_id: string
  title: string
  description?: string
  category?: string
  expires_in_hours?: number
  initial_odds_yes?: number
}

export async function createMarket(roomId: string, data: Omit<CreateMarketRequest, 'room_id'>): Promise<Market> {
  return apiCall('/markets', {
    method: 'POST',
    body: JSON.stringify({ ...data, room_id: roomId }),
  })
}

export async function getMarkets(roomId: string): Promise<Market[]> {
  return apiCall(`/markets?room_id=${roomId}`, { method: 'GET' })
}

export async function getMarket(marketId: string): Promise<Market> {
  return apiCall(`/markets/${marketId}`, { method: 'GET' })
}

// ============================================================================
// TRADING
// ============================================================================

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

export async function placeTrade(
  marketId: string,
  data: TradeRequest
): Promise<TradeResponse> {
  return apiCall(`/markets/${marketId}/trade`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getMarketTrades(marketId: string): Promise<any[]> {
  return apiCall(`/markets/${marketId}/trades`, { method: 'GET' })
}

// Alias for compatibility
export const getTrades = getMarketTrades

export async function getUserPositions(roomId: string): Promise<any[]> {
  return apiCall(`/markets/my-positions?room_id=${roomId}`, { method: 'GET' })
}

export async function getPosition(marketId: string): Promise<any> {
  // Get user's position for a specific market
  // Backend doesn't have this endpoint, so we'll return null for now
  // Position will be calculated on frontend or added to market detail response
  return null
}

export async function previewTrade(marketId: string, data: TradeRequest): Promise<any> {
  // Preview trade without executing
  // Calculate expected shares and new odds
  // This should be added to backend, for now return estimate
  const market = await getMarket(marketId)

  // Simple LMSR preview calculation (approximate)
  const newOdds = data.side === 'yes'
    ? Math.min(0.99, market.odds_yes + (data.amount / market.total_pool) * 0.1)
    : Math.min(0.99, market.odds_no + (data.amount / market.total_pool) * 0.1)

  const shares = data.amount / (data.side === 'yes' ? market.odds_yes : market.odds_no)

  return {
    shares_received: shares,
    new_odds_yes: data.side === 'yes' ? newOdds : market.odds_yes,
    new_odds_no: data.side === 'no' ? newOdds : market.odds_no,
  }
}

// ============================================================================
// VOTING & RESOLUTION
// ============================================================================

export interface VoteRequest {
  vote: 'yes' | 'no'
}

export async function submitVote(marketId: string, vote: 'yes' | 'no'): Promise<any> {
  return apiCall(`/markets/${marketId}/vote`, {
    method: 'POST',
    body: JSON.stringify({ vote }),
  })
}

export async function getMarketVotes(marketId: string): Promise<any> {
  return apiCall(`/markets/${marketId}/votes`, { method: 'GET' })
}

// Alias for compatibility
export const getVotes = getMarketVotes

export async function resolveMarket(marketId: string, result: 'yes' | 'no'): Promise<any> {
  return apiCall(`/markets/${marketId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ result }),
  })
}

// ============================================================================
// PROPHET AI
// ============================================================================

export async function generateMarkets(roomId: string): Promise<any> {
  return apiCall(`/prophet/generate-markets/${roomId}`, {
    method: 'POST',
  })
}

// Alias for backward compatibility
export const generateMarketsWithProphet = generateMarkets

export async function getProphetStatus(): Promise<any> {
  return apiCall('/prophet/status', { method: 'GET' })
}

export async function getProphetBets(roomId: string): Promise<any[]> {
  // TODO: Add backend endpoint for this
  // For now, return empty array
  return []
}

// ============================================================================
// CHAINED MARKETS
// ============================================================================

export interface CreateChainedMarketRequest {
  parent_market_id: string
  trigger_condition: 'parent_resolves_yes' | 'parent_resolves_no'
  title: string
  description?: string
  category?: string
  initial_odds_yes?: number
}

export async function createChainedMarket(data: CreateChainedMarketRequest): Promise<any> {
  return apiCall('/markets/chains/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getChainTree(marketId: string): Promise<any> {
  return apiCall(`/markets/${marketId}/chain-tree`, { method: 'GET' })
}

export async function getMarketChildren(marketId: string): Promise<any> {
  return apiCall(`/markets/${marketId}/children`, { method: 'GET' })
}

// ============================================================================
// DERIVATIVE MARKETS
// ============================================================================

export interface CreateDerivativeRequest {
  reference_market_id: string
  threshold_type: 'odds_threshold' | 'volume_threshold' | 'resolution_method'
  threshold_value: string
  threshold_deadline?: string
  initial_odds_yes?: number
  auto_title?: boolean
  custom_title?: string
  description?: string
}

export async function createDerivative(data: CreateDerivativeRequest): Promise<any> {
  return apiCall('/markets/derivatives/create', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function getDerivativeStatus(marketId: string): Promise<any> {
  return apiCall(`/markets/${marketId}/derivative-status`, { method: 'GET' })
}

// ============================================================================
// USER STATS
// ============================================================================

export async function getUserStats(): Promise<any> {
  return apiCall('/users/me/stats', { method: 'GET' })
}

export async function getUserProfile(): Promise<any> {
  return apiCall('/users/me', { method: 'GET' })
}
