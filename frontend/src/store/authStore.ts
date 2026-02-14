import { create } from 'zustand'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url: string | null
  clout_score: number
  clout_rank: string
  total_bets_placed: number
  total_bets_won: number
  streak_current: number
  balance_virtual: number
  balance_cash: number
  wallet_address: string | null
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
            balance_virtual: virtual ?? state.user.balance_virtual,
            balance_cash: cash ?? state.user.balance_cash,
          }
        : null,
    })),
}))
