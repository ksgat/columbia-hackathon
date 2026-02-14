# Prophecy Frontend

Social prediction markets platform built with Next.js, React, and TypeScript.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3.x
- **Animations**: Framer Motion
- **Charts**: Recharts
- **State Management**: Zustand
- **Real-time**: Supabase JS Client
- **Auth**: Privy React SDK
- **HTTP Client**: Axios

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Update `.env.local` with your credentials:

```env
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Privy (Wallet Auth)
NEXT_PUBLIC_PRIVY_APP_ID=your_privy_app_id_here
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── page.tsx              # Landing page (/)
│   │   ├── home/                 # Home feed (/home)
│   │   ├── room/[id]/            # Room view (/room/:id)
│   │   ├── market/[id]/          # Market detail (/market/:id)
│   │   └── profile/[id]/         # User profile (/profile/:id)
│   ├── components/
│   │   ├── market/               # Market-related components
│   │   │   ├── MarketCard.tsx
│   │   │   ├── OddsBar.tsx
│   │   │   ├── OddsChart.tsx
│   │   │   ├── TradePanel.tsx
│   │   │   ├── VotePanel.tsx
│   │   │   ├── ChainTree.tsx
│   │   │   └── DerivativeLink.tsx
│   │   ├── feed/                 # Feed components
│   │   │   ├── LiveTicker.tsx
│   │   │   ├── NarrativeCard.tsx
│   │   │   └── AnomalyAlert.tsx
│   │   ├── room/                 # Room components
│   │   │   ├── RoomCard.tsx
│   │   │   ├── LeaderboardRow.tsx
│   │   │   ├── WhisperForm.tsx
│   │   │   └── SpectatorBanner.tsx
│   │   ├── profile/              # Profile components
│   │   │   ├── BadgeDisplay.tsx
│   │   │   └── HedgeCard.tsx
│   │   ├── vibe/                 # Vibe Check components
│   │   │   ├── VibeGauge.tsx
│   │   │   ├── TopicRadar.tsx
│   │   │   ├── ActivityHeatmap.tsx
│   │   │   └── RivalryCard.tsx
│   │   └── shared/               # Shared components
│   │       ├── UserAvatar.tsx
│   │       ├── Button.tsx
│   │       ├── Modal.tsx
│   │       └── Layout.tsx
│   ├── hooks/                    # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useSupabaseRealtime.ts
│   │   ├── useWebSocket.ts
│   │   └── useMarket.ts
│   ├── store/                    # Zustand stores
│   │   ├── authStore.ts
│   │   ├── roomStore.ts
│   │   ├── marketStore.ts
│   │   └── tickerStore.ts
│   └── lib/                      # Utility libraries
│       ├── api.ts                # API client functions
│       ├── supabase.ts           # Supabase client setup
│       └── privy.ts              # Privy auth config
├── public/                       # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Key Features

### 🏠 Landing Page
- Animated hero section with gradient background
- Feature showcase cards
- Google OAuth login via Privy

### 📊 Home Feed
- Room selector tabs
- Live market cards with odds bars
- Quick bet actions

### 🎯 Market Detail
- Real-time odds chart
- Trade panel with estimated payouts
- Market info and status
- Vote panel (during resolution phase)

### 🏆 Room View
- Room header with stats
- Tabbed interface (Markets, Feed, Leaderboard)
- Market creation

### 👤 User Profile
- Achievement badges
- Open positions
- Prophet's hedge suggestions
- Recent activity

### 📈 Vibe Check Dashboard
- Optimism gauge (speedometer)
- Topic distribution radar chart
- Activity heatmap
- Rivalry cards

## Real-time Features

The app uses Supabase real-time subscriptions for live updates:

- **Markets**: Odds changes, status updates
- **Trades**: New trades appear instantly
- **Narrative Events**: Prophet commentary
- **Votes**: Resolution vote tallies

## API Integration

All API calls are centralized in `src/lib/api.ts`:

```typescript
import { marketApi } from '@/lib/api'

// Place a trade
const result = await marketApi.trade(marketId, 'yes', 100)

// Get room feed
const feed = await roomApi.getFeed(roomId)
```

## State Management

Global state is managed with Zustand:

```typescript
import { useAuthStore } from '@/store/authStore'

const { user, setUser } = useAuthStore()
```

## Styling

- **Tailwind CSS** for utility-first styling
- **Custom colors** defined in `tailwind.config.js`:
  - Primary: `#8B5CF6` (purple)
  - Secondary: `#EC4899` (pink)
  - Accent: `#10B981` (green)
  - Dark: `#0F172A`
  - Darker: `#020617`
- **Framer Motion** for animations

## Building for Production

```bash
npm run build
npm start
```

## Notes

- Make sure the backend is running on `http://localhost:8000`
- Supabase must be configured with the correct schema
- Privy app must be set up for authentication
- Some features require the backend AI agents to be operational

## Next Steps

1. ✅ Core pages and components
2. ⏳ Additional pages (Vibe Check, Profile, Settings)
3. ⏳ More market components (OddsChart, VotePanel, ChainTree)
4. ⏳ WebSocket integration for live ticker
5. ⏳ Create room flow
6. ⏳ Market creation flow

## Support

For issues or questions, check the main PROPHECY_SPEC.md file.
