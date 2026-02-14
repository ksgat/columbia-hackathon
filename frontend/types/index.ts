export interface User {
  id: string
  phoneNumber: string
  displayName: string
  balance: number // Paper money balance
}

export interface Market {
  id: string
  creatorId: string
  groupName: string // "#friend group 1"
  participants: string[] // Array of user IDs
  createdAt: Date
}

export interface Prediction {
  id: string
  marketId: string
  question: string // "will friend x do y"
  creatorId: string
  status: 'open' | 'closed' | 'resolved'
  resolution?: 'yes' | 'no' // Final outcome
  yesPool: number // Total $ bet on yes
  noPool: number // Total $ bet on no
  createdAt: Date
}

export interface Bet {
  id: string
  predictionId: string
  userId: string
  amount: number
  position: 'yes' | 'no'
  placedAt: Date
}

export interface BettingState {
  users: Record<string, User>
  markets: Record<string, Market>
  predictions: Record<string, Prediction>
  bets: Bet[]
}
