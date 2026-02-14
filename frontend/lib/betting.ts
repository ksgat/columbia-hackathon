import { BettingState, User, Market, Prediction, Bet } from '@/types'

const STARTING_BALANCE = 100 // Each user starts with $100
const STORAGE_KEY = 'betting_state'

// Initialize or load state from localStorage
export function loadState(): BettingState {
  if (typeof window === 'undefined') return getEmptyState()
  
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    const parsed = JSON.parse(stored)
    // Convert date strings back to Date objects
    Object.values(parsed.markets).forEach((m: any) => {
      m.createdAt = new Date(m.createdAt)
    })
    Object.values(parsed.predictions).forEach((p: any) => {
      p.createdAt = new Date(p.createdAt)
    })
    parsed.bets.forEach((b: any) => {
      b.placedAt = new Date(b.placedAt)
    })
    return parsed
  }
  return getEmptyState()
}

export function saveState(state: BettingState): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function getEmptyState(): BettingState {
  return {
    users: {},
    markets: {},
    predictions: {},
    bets: []
  }
}

// User Operations
export function createUser(phoneNumber: string, displayName: string): User {
  const state = loadState()
  
  const user: User = {
    id: crypto.randomUUID(),
    phoneNumber,
    displayName,
    balance: STARTING_BALANCE
  }
  
  state.users[user.id] = user
  saveState(state)
  
  return user
}

export function getUser(userId: string): User | null {
  const state = loadState()
  return state.users[userId] || null
}

export function getUserByPhone(phoneNumber: string): User | null {
  const state = loadState()
  return Object.values(state.users).find(u => u.phoneNumber === phoneNumber) || null
}

export function updateUserBalance(userId: string, amount: number): User {
  const state = loadState()
  const user = state.users[userId]
  
  if (!user) throw new Error('User not found')
  
  user.balance += amount
  saveState(state)
  
  return user
}

// Market Operations
export function createMarket(creatorId: string, groupName: string, participantPhones: string[]): Market {
  const state = loadState()
  
  const market: Market = {
    id: crypto.randomUUID(),
    creatorId,
    groupName,
    participants: [creatorId], // Creator auto-added
    createdAt: new Date()
  }
  
  state.markets[market.id] = market
  saveState(state)
  
  return market
}

export function getMarket(marketId: string): Market | null {
  const state = loadState()
  return state.markets[marketId] || null
}

export function getUserMarkets(userId: string): Market[] {
  const state = loadState()
  return Object.values(state.markets).filter(m => 
    m.participants.includes(userId) || m.creatorId === userId
  )
}

export function addParticipant(marketId: string, userId: string): Market {
  const state = loadState()
  const market = state.markets[marketId]
  
  if (!market) throw new Error('Market not found')
  if (!market.participants.includes(userId)) {
    market.participants.push(userId)
  }
  
  saveState(state)
  return market
}

// Prediction Operations
export function createPrediction(marketId: string, creatorId: string, question: string): Prediction {
  const state = loadState()
  
  const prediction: Prediction = {
    id: crypto.randomUUID(),
    marketId,
    question,
    creatorId,
    status: 'open',
    yesPool: 0,
    noPool: 0,
    createdAt: new Date()
  }
  
  state.predictions[prediction.id] = prediction
  saveState(state)
  
  return prediction
}

export function getPrediction(predictionId: string): Prediction | null {
  const state = loadState()
  return state.predictions[predictionId] || null
}

export function getMarketPredictions(marketId: string): Prediction[] {
  const state = loadState()
  return Object.values(state.predictions).filter(p => p.marketId === marketId)
}

// Betting Operations
export function placeBet(
  userId: string, 
  predictionId: string, 
  amount: number, 
  position: 'yes' | 'no'
): { bet: Bet, prediction: Prediction, user: User } {
  const state = loadState()
  
  const user = state.users[userId]
  const prediction = state.predictions[predictionId]
  
  if (!user) throw new Error('User not found')
  if (!prediction) throw new Error('Prediction not found')
  if (prediction.status !== 'open') throw new Error('Prediction is closed')
  if (user.balance < amount) throw new Error('Insufficient balance')
  if (amount <= 0) throw new Error('Bet amount must be positive')
  
  // Check if user already bet on this prediction
  const existingBet = state.bets.find(
    b => b.userId === userId && b.predictionId === predictionId
  )
  if (existingBet) throw new Error('Already bet on this prediction')
  
  // Deduct from balance
  user.balance -= amount
  
  // Add to pool
  if (position === 'yes') {
    prediction.yesPool += amount
  } else {
    prediction.noPool += amount
  }
  
  // Create bet
  const bet: Bet = {
    id: crypto.randomUUID(),
    predictionId,
    userId,
    amount,
    position,
    placedAt: new Date()
  }
  
  state.bets.push(bet)
  saveState(state)
  
  return { bet, prediction, user }
}

export function getUserBets(userId: string, predictionId?: string): Bet[] {
  const state = loadState()
  return state.bets.filter(b => 
    b.userId === userId && (!predictionId || b.predictionId === predictionId)
  )
}

export function getPredictionBets(predictionId: string): Bet[] {
  const state = loadState()
  return state.bets.filter(b => b.predictionId === predictionId)
}

// Odds Calculation
export function calculateOdds(prediction: Prediction): { yesOdds: number, noOdds: number } {
  const total = prediction.yesPool + prediction.noPool
  
  if (total === 0) {
    return { yesOdds: 50, noOdds: 50 }
  }
  
  const yesOdds = (prediction.yesPool / total) * 100
  const noOdds = (prediction.noPool / total) * 100
  
  return { 
    yesOdds: Math.round(yesOdds), 
    noOdds: Math.round(noOdds) 
  }
}

// Resolution (for later)
export function resolvePrediction(
  predictionId: string, 
  resolution: 'yes' | 'no'
): { prediction: Prediction, payouts: Array<{ userId: string, amount: number }> } {
  const state = loadState()
  
  const prediction = state.predictions[predictionId]
  if (!prediction) throw new Error('Prediction not found')
  if (prediction.status === 'resolved') throw new Error('Already resolved')
  
  prediction.status = 'resolved'
  prediction.resolution = resolution
  
  const totalPool = prediction.yesPool + prediction.noPool
  const winningPool = resolution === 'yes' ? prediction.yesPool : prediction.noPool
  
  // Calculate payouts for winners
  const payouts: Array<{ userId: string, amount: number }> = []
  
  if (winningPool > 0) {
    state.bets
      .filter(b => b.predictionId === predictionId && b.position === resolution)
      .forEach(bet => {
        const winnerShare = bet.amount / winningPool
        const payout = totalPool * winnerShare
        
        const user = state.users[bet.userId]
        if (user) {
          user.balance += payout
          payouts.push({ userId: user.id, amount: payout })
        }
      })
  }
  
  saveState(state)
  
  return { prediction, payouts }
}

// Utility: Reset everything (for testing)
export function resetState(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(STORAGE_KEY)
}
