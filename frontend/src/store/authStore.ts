import { create } from 'zustand'

interface User {
  id: string
  email: string
  display_name: string
  is_npc: boolean
  tokens: number
  total_trades: number
  successful_predictions: number
  created_at: string
  updated_at: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User) => void
  clearUser: () => void
  updateBalance: (virtual?: number, cash?: number) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: true }),
  clearUser: () => set({ user: null, isAuthenticated: false }),
  updateBalance: (virtual, cash) =>
    set((state) => ({
      user: state.user
        ? {
            ...state.user,
            tokens: virtual ?? state.user.tokens,
          }
        : null,
    })),
}))
