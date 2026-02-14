# Prediction Market - Frontend Implementation Plan

## Overview
Based on your wireframe, this is a pure frontend implementation with paper money (fake balances). Backend integration comes later via API routes.

## User Flow (From Wireframe)

### Friend 1 (Market Creator)
1. Land on home → Click "add market"
2. Create market → Enter "#friend group 1" 
3. Add phone numbers → Click "+"
4. Confirmation screen → "click here to add to groupchat"
5. See market with predictions → Create individual predictions like "will friend x do y"
6. Each prediction shows green/red split (yes/no odds)

### Friend 2 (Invited User)
1. Click invite link (via SMS/groupchat)
2. If new: Enter phone number + name (only if number not recognized)
3. If returning: Auto-authenticated
4. View market → See all predictions
5. Click prediction → See odds, place bet
6. Create new predictions on existing markets

## Tech Stack
- **Framework**: Next.js 16 (latest version)
- **Styling**: Tailwind CSS
- **Database**: Supabase (Tell me how tables )
- **Auth**: Phone number stored in supabase (thats it no password type shit magic link requires phone number)
## File Structure

```
/app
  /(routes)
    page.tsx                    # Landing page (add market button)
    /create
      page.tsx                  # Create market form
    /market
      /[id]
        page.tsx                # Market view + predictions list
        /prediction/[predId]
          page.tsx              # Individual prediction betting view
    /invite/[token]
      page.tsx                  # Invite landing (phone/name capture)
  layout.tsx
  globals.css

/components
  /ui
    button.tsx                  # Reusable button
    input.tsx                   # Form inputs
    card.tsx                    # Card wrapper
  market-card.tsx               # Market summary card
  prediction-card.tsx           # Individual prediction (green/red split)
  phone-input.tsx               # Phone number input with + button
  bet-modal.tsx                 # Betting interface overlay
  odds-display.tsx              # Green/red bar showing odds
  group-invite-button.tsx       # "Add to groupchat" button
  balance-display.tsx           # Shows user's current balance

/lib
  betting.ts                    # Paper money logic (THE CORE FILE)
  storage.ts                    # localStorage helpers
  utils.ts                      # Utility functions
  mock-data.ts                  # Sample markets for testing

/types
  index.ts                      # TypeScript interfaces

/contexts
  AuthContext.tsx               # User phone/name state
  MarketContext.tsx             # Markets and predictions state
```

## Data Models (TypeScript)

```typescript
// types/index.ts

export interface User {
  id: string
  phoneNumber: string
  displayName: string
  balance: number                // Paper money balance
}

export interface Market {
  id: string
  creatorId: string
  groupName: string              // "#friend group 1"
  participants: string[]         // Array of user IDs
  createdAt: Date
}

export interface Prediction {
  id: string
  marketId: string
  question: string               // "will friend x do y"
  creatorId: string
  status: 'open' | 'closed' | 'resolved'
  resolution?: 'yes' | 'no'      // Final outcome
  yesPool: number                // Total $ bet on yes
  noPool: number                 // Total $ bet on no
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
```

## Core Logic: betting.ts

This file handles ALL money operations with fake currency.

```typescript
// lib/betting.ts

import { BettingState, User, Market, Prediction, Bet } from '@/types'

const STARTING_BALANCE = 100 // Each user starts with $100
const STORAGE_KEY = 'betting_state'

// Initialize or load state from localStorage
export function loadState(): BettingState {
  if (typeof window === 'undefined') return getEmptyState()
  
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    return JSON.parse(stored)
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
  
  saveState(state)
  
  return { prediction, payouts }
}

// Utility: Reset everything (for testing)
export function resetState(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(STORAGE_KEY)
}
```

## Component Specifications

### 1. Landing Page (`app/page.tsx`)
```typescript
// Simple landing with "Create Market" button
- Hero text: "Bet on your friends"
- Big CTA button → /create
- (Optional) List of your markets if authenticated
```

### 2. Create Market (`app/create/page.tsx`)
```typescript
// Market creation form
Components needed:
- Input for group name ("#friend group 1")
- PhoneInput component (with + button to add multiple)
- Submit button
- On submit: createMarket() → redirect to /market/[id]
```

### 3. Phone Input Component (`components/phone-input.tsx`)
```typescript
// Manages list of phone numbers with + button
State:
- phones: string[]
- currentInput: string

Features:
- Text input for phone number
- "+" button to add to list
- Display list of added phones with remove (x) option
- Validation (basic format check)
```

### 4. Market View (`app/market/[id]/page.tsx`)
```typescript
// Main market dashboard
Shows:
- Group name header
- "Create prediction" button (prominent)
- List of PredictionCard components
- Balance display in corner

On load:
- getMarket(id)
- getMarketPredictions(id)
```

### 5. Prediction Card (`components/prediction-card.tsx`)
```typescript
// Individual prediction display
Props: prediction: Prediction

Shows:
- Question text
- OddsDisplay component (green/red bar)
- Total pool size
- "Bet" button → Navigate to /market/[id]/prediction/[predId]

Visual:
- Card with green left side (yes %) and red right side (no %)
- Percentages displayed
```

### 6. Odds Display (`components/odds-display.tsx`)
```typescript
// Visual representation of yes/no odds
Props: 
- yesOdds: number (0-100)
- noOdds: number (0-100)

Render:
- Horizontal bar split by percentage
- Green section (yes) | Red section (no)
- Labels showing percentages
- Total pool amount below
```

### 7. Betting View (`app/market/[id]/prediction/[predId]/page.tsx`)
```typescript
// Full-screen betting interface
Shows:
- Prediction question (large)
- Current odds (OddsDisplay)
- Your balance
- Amount input slider/buttons
- YES / NO buttons (big, green/red)
- Confirm bet modal

Flow:
1. User selects amount
2. User clicks YES or NO
3. Modal: "Confirm $X on YES?"
4. On confirm: placeBet() → show success → redirect back
```

### 8. Bet Modal (`components/bet-modal.tsx`)
```typescript
// Confirmation overlay
Props:
- amount: number
- position: 'yes' | 'no'
- onConfirm: () => void
- onCancel: () => void

Shows:
- "Bet $X on [YES/NO]?"
- Confirm / Cancel buttons
- Quick animation on confirm
```

### 9. Invite Landing (`app/invite/[token]/page.tsx`)
```typescript
// For new users clicking invite link
Flow:
1. Check if user exists (via phone in localStorage)
2. If yes: Auto-authenticate → redirect to market
3. If no: Show form
   - Phone number input
   - Display name input
   - Submit → createUser() → addParticipant() → redirect to market

Form:
- "What is your phone number?"
- "What is your name?"
- Submit button
- Note: "only give this option if the number is valid (ie they're logged in)"
```

### 10. Balance Display (`components/balance-display.tsx`)
```typescript
// Shows user's current balance
Props: userId: string

Shows:
- "$XX.XX" in corner
- Green if positive, red if low
- Small, unobtrusive
```

### 11. Group Invite Button (`components/group-invite-button.tsx`)
```typescript
// "Add to groupchat" functionality
Props: marketId: string

Features:
- Generates shareable link
- Copy to clipboard
- Shows "Copied!" toast
- Link format: /invite/[marketId]-[token]
```

## Context Providers

### AuthContext (`contexts/AuthContext.tsx`)
```typescript
// Manages current user state
State:
- currentUser: User | null
- isAuthenticated: boolean

Methods:
- login(phoneNumber: string, displayName?: string)
- logout()
- updateBalance(amount: number)

Persists:
- userId in localStorage
- Auto-loads on mount
```

### MarketContext (`contexts/MarketContext.tsx`)
```typescript
// Manages markets and predictions (optional, can just use component state)
State:
- markets: Market[]
- predictions: Prediction[]

Methods:
- refreshMarket(marketId: string)
- refreshPredictions(marketId: string)

Could skip this and just use direct betting.ts calls in components
```

## Styling Guidelines (Tailwind)

### Color Palette
```css
/* Dark mode base */
bg-zinc-950       /* Background */
bg-zinc-900       /* Cards */
text-white        /* Primary text */
text-zinc-400     /* Secondary text */

/* Accent colors */
text-green-500    /* YES / Positive */
bg-green-500/20   /* YES background */
text-red-500      /* NO / Negative */
bg-red-500/20     /* NO background */

/* Neon accent */
text-cyan-400     /* Highlights */
border-cyan-500   /* Active borders */
```

### Component Styles

**Buttons:**
```tsx
// Primary
className="bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-3 rounded-lg font-semibold"

// YES button
className="bg-green-500 hover:bg-green-600 text-white flex-1 py-4 rounded-lg text-xl font-bold"

// NO button  
className="bg-red-500 hover:bg-red-600 text-white flex-1 py-4 rounded-lg text-xl font-bold"
```

**Cards:**
```tsx
className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 hover:border-zinc-700 transition"
```

**Inputs:**
```tsx
className="bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-white focus:border-cyan-500 focus:outline-none"
```

## Mock Data for Testing

```typescript
// lib/mock-data.ts
export function seedMockData() {
  // Create test users
  const jake = createUser('+15551234567', 'Jake')
  const alex = createUser('+15559876543', 'Alex')
  const sarah = createUser('+15555555555', 'Sarah')
  
  // Create test market
  const market = createMarket(jake.id, '#friend group 1', [])
  addParticipant(market.id, alex.id)
  addParticipant(market.id, sarah.id)
  
  // Create test predictions
  const pred1 = createPrediction(market.id, jake.id, 'Will Jake show up to brunch?')
  const pred2 = createPrediction(market.id, alex.id, 'Will Alex be on time?')
  
  // Place some bets
  placeBet(alex.id, pred1.id, 20, 'no')  // Alex bets Jake won't show
  placeBet(sarah.id, pred1.id, 10, 'yes') // Sarah bets Jake will show
  
  return { market, predictions: [pred1, pred2] }
}
```

## Page-by-Page Implementation Order

1. **Start with betting.ts** - Get the core logic working first
2. **Build Landing + Create Market** - Basic flow
3. **Market View + Prediction Cards** - Display logic
4. **Betting Interface** - The money shot
5. **Invite Flow** - User onboarding
6. **Polish** - Animations, toasts, balance display

## Key Features to Nail for Demo

### Must Have:
- ✅ Create market with phone numbers
- ✅ Place bets on predictions
- ✅ Real-time odds update (just re-render)
- ✅ Balance tracking
- ✅ Green/red visual split

### Nice to Have:
- ⏰ Animations on bet placement
- ⏰ Sound effects
- ⏰ Share button with link copy
- ⏰ Mobile responsive

### Skip for Now:
- ❌ SMS integration (backend)
- ❌ Resolution/payouts UI
- ❌ History/past bets view
- ❌ Real authentication

## Testing Flow

1. Open app → Create market
2. Add 2-3 phone numbers
3. Create 2-3 predictions
4. Open in multiple tabs (simulate different users via phone input)
5. Place bets from different "users"
6. Watch odds shift

## Environment Setup

```bash
# Create Next.js app
npx create-next-app@latest prediction-market --typescript --tailwind --app

# Install dependencies
npm install lucide-react  # Icons
npm install clsx          # Conditional classes

# Run dev server
npm run dev
```

## Notes

- Everything is stored in localStorage (wipes on clear)
- No backend calls needed yet
- Phone numbers are identifiers (no validation)
- Balance is just integers ($100 = 100, no cents)
- "Magic links" are just /invite/[marketId] that auto-add participants
- Resolution can be manual for demo (just call resolvePrediction in console)

## Backend Integration (Later)

When ready to add backend:
1. Replace all betting.ts functions with API calls
2. Keep the same function signatures
3. Add loading states
4. Handle errors with toasts

```typescript
// Future: lib/api.ts
export async function placeBet(userId, predictionId, amount, position) {
  const res = await fetch('/api/bets/place', {
    method: 'POST',
    body: JSON.stringify({ userId, predictionId, amount, position })
  })
  return res.json()
}
```

But for now, keep it simple with localStorage.

---

This should give you everything you need to build the frontend in Cursor. Focus on getting the core betting flow working first, then polish the UI.