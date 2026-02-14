import { create } from 'zustand'

interface Market {
  id: string
  room_id: string
  title: string
  odds_yes: number
  odds_no: number
  status: string
  total_pool: number
  expires_at: string
}

interface MarketState {
  markets: Market[]
  setMarkets: (markets: Market[]) => void
  addMarket: (market: Market) => void
  updateMarket: (marketId: string, updates: Partial<Market>) => void
  removeMarket: (marketId: string) => void
}

export const useMarketStore = create<MarketState>((set) => ({
  markets: [],
  setMarkets: (markets) => set({ markets }),
  addMarket: (market) => set((state) => ({ markets: [market, ...state.markets] })),
  updateMarket: (marketId, updates) =>
    set((state) => ({
      markets: state.markets.map((m) => (m.id === marketId ? { ...m, ...updates } : m)),
    })),
  removeMarket: (marketId) =>
    set((state) => ({ markets: state.markets.filter((m) => m.id !== marketId) })),
}))
