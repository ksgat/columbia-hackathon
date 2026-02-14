import { create } from 'zustand'

interface Room {
  id: string
  name: string
  description: string | null
  slug: string
  join_code: string
  creator_id: string
  is_public: boolean
  status: string
  max_members: number
  theme_color: string | null
  cover_image: string | null
  member_count: number
  market_count: number
  total_volume: number
  created_at: string
  updated_at: string
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
