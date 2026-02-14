import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth endpoints
export const authApi = {
  login: (token: string) => api.post('/auth/login', { token }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

// User endpoints
export const userApi = {
  getUser: (id: string) => api.get(`/users/${id}`),
  updateUser: (id: string, data: any) => api.patch(`/users/${id}`, data),
  getPortfolio: (id: string) => api.get(`/users/${id}/portfolio`),
  getAchievements: (id: string) => api.get(`/users/${id}/achievements`),
  getStats: (id: string) => api.get(`/users/${id}/stats`),
  getHedgeSuggestions: (id: string, roomId: string) =>
    api.get(`/users/${id}/hedge-suggestions`, { params: { room_id: roomId } }),
}

// Room endpoints
export const roomApi = {
  createRoom: (data: any) => api.post('/rooms', data),
  getRooms: () => api.get('/rooms'),
  getRoom: (id: string) => api.get(`/rooms/${id}`),
  joinRoom: (id: string, joinCode: string, role: string = 'participant') =>
    api.post(`/rooms/${id}/join`, { join_code: joinCode, role }),
  leaveRoom: (id: string) => api.post(`/rooms/${id}/leave`),
  getLeaderboard: (id: string) => api.get(`/rooms/${id}/leaderboard`),
  getFeed: (id: string, cursor?: string) =>
    api.get(`/rooms/${id}/feed`, { params: { cursor } }),
  getVibeCheck: (id: string) => api.get(`/rooms/${id}/vibe-check`),
  getMembers: (id: string) => api.get(`/rooms/${id}/members`),
  updateSettings: (id: string, data: any) => api.patch(`/rooms/${id}/settings`, data),
}

// Market endpoints
export const marketApi = {
  createMarket: (data: any) => api.post('/markets', data),
  getMarket: (id: string) => api.get(`/markets/${id}`),
  getTrades: (id: string, page: number = 1) =>
    api.get(`/markets/${id}/trades`, { params: { page } }),
  getChain: (id: string) => api.get(`/markets/${id}/chain`),
  getDerivatives: (id: string) => api.get(`/markets/${id}/derivatives`),
  trade: (id: string, side: 'yes' | 'no', amount: number) =>
    api.post(`/markets/${id}/trade`, { side, amount }),
  getVotes: (id: string) => api.get(`/markets/${id}/votes`),
  vote: (id: string, vote: 'yes' | 'no') =>
    api.post(`/markets/${id}/vote`, { vote }),
  cancel: (id: string) => api.post(`/markets/${id}/cancel`),
}

// Whisper endpoints
export const whisperApi = {
  submit: (roomId: string, data: any) => api.post(`/rooms/${roomId}/whispers`, data),
  getPending: (roomId: string) => api.get(`/rooms/${roomId}/whispers/pending`),
  approve: (id: string) => api.post(`/whispers/${id}/approve`),
  reject: (id: string) => api.post(`/whispers/${id}/reject`),
}

// Payment endpoints
export const paymentApi = {
  deposit: (amount: number) => api.post('/payments/deposit', { amount }),
  getDepositStatus: (id: string) => api.get(`/payments/deposit/${id}/status`),
  withdraw: (amount: number, address: string) =>
    api.post('/payments/withdraw', { amount, destination_address: address }),
  getBalance: () => api.get('/payments/balance'),
  getHistory: () => api.get('/payments/history'),
}
