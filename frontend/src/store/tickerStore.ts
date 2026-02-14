import { create } from 'zustand'

interface TickerItem {
  market_id: string
  title: string
  odds_yes: number
  change_1h: number
  volume_1h: number
  is_hot: boolean
  is_new: boolean
  status: string
}

interface TickerState {
  items: TickerItem[]
  setItems: (items: TickerItem[]) => void
  addItem: (item: TickerItem) => void
  updateItem: (marketId: string, updates: Partial<TickerItem>) => void
}

export const useTickerStore = create<TickerState>((set) => ({
  items: [],
  setItems: (items) => set({ items }),
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  updateItem: (marketId, updates) =>
    set((state) => ({
      items: state.items.map((i) => (i.market_id === marketId ? { ...i, ...updates } : i)),
    })),
}))
