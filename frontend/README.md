# Prediction Market - Frontend

A Next.js-based prediction market application where friends can bet on predictions using paper money.

## Features Implemented ✅

### Core Functionality
- **Market Creation**: Create markets with group names and add phone numbers of friends
- **Prediction Creation**: Add predictions to markets with yes/no questions
- **Betting System**: Place bets on predictions with a slider interface
- **Real-time Odds**: Odds update dynamically based on bet distribution
- **Balance Tracking**: Each user starts with $100 in play money
- **Invite System**: Share markets via invite links

### Pages
1. **Landing Page** (`/`) - Hero with "Create Market" button
2. **Create Market** (`/create`) - Form to create a new market with group name and phone numbers
3. **Market View** (`/market/[id]`) - View market predictions, create new predictions, share market
4. **Betting Page** (`/market/[id]/prediction/[predId]`) - Place bets with amount selection and YES/NO buttons
5. **Invite Page** (`/invite/[marketId]`) - Join market with phone and name

### UI Components
- **Button**: Multiple variants (primary, plus, ghost, green, red)
- **Input**: Styled text inputs with focus states
- **Card**: Container components for content
- **PhoneInput**: Add multiple phone numbers with + button
- **PredictionCard**: Display predictions with green/red odds visualization

### State Management
- localStorage-based state persistence
- No backend required - fully functional frontend demo
- Automatic user creation on first visit

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Styling**: Tailwind CSS v4
- **TypeScript**: Full type safety
- **Icons**: Lucide React
- **UI**: shadcn-inspired components

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Usage Flow

1. Click "Create Market" on landing page
2. Enter a group name (e.g., "#Columbia Hackathon Friends")
3. Add phone numbers of friends (optional)
4. Create predictions by clicking "Create Prediction"
5. Place bets on predictions by selecting amount and YES/NO
6. Watch odds update in real-time
7. Share market with friends using the Share button

## Demo Flow

The app automatically creates a demo user on first visit with $100 balance. You can:
- Create multiple markets
- Add predictions to markets
- Place bets and watch odds change
- Track your balance as you bet

## Data Models

All data is stored in localStorage under the key `betting_state`:

- **Users**: Phone number, display name, balance
- **Markets**: Group name, participants, creator
- **Predictions**: Question, status, yes/no pools
- **Bets**: User, amount, position (yes/no)

## Design Features

- Dark theme with zinc color palette
- Cyan accent color for CTAs
- Green for YES, Red for NO
- Smooth transitions and hover states
- Mobile-responsive design
- Clean, modern UI

## Future Enhancements

- Backend integration with API routes
- SMS integration for invites
- Prediction resolution and payouts
- User authentication
- Bet history view
- Multiple currency support
