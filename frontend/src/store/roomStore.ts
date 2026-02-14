import { create } from 'zustand'

interface Room {
  id: string
  name: string
  description: string
  join_code: string
  currency_mode: 'virtual' | 'cash'
  min_bet: number
  max_bet: number
  is_active: boolean
  member_count?: number
  spectator_count?: number
}

interface RoomState {
  rooms: Room[]
  currentRoom: Room | null
  setRooms: (rooms: Room[]) => void
  addRoom: (room: Room) => void
  setCurrentRoom: (room: Room | null) => void
  updateRoom: (roomId: string, updates: Partial<Room>) => void
}

export const useRoomStore = create<RoomState>((set) => ({
  rooms: [],
  currentRoom: null,
  setRooms: (rooms) => set({ rooms }),
  addRoom: (room) => set((state) => ({ rooms: [...state.rooms, room] })),
  setCurrentRoom: (room) => set({ currentRoom: room }),
  updateRoom: (roomId, updates) =>
    set((state) => ({
      rooms: state.rooms.map((r) => (r.id === roomId ? { ...r, ...updates } : r)),
      currentRoom:
        state.currentRoom?.id === roomId
          ? { ...state.currentRoom, ...updates }
          : state.currentRoom,
    })),
}))
