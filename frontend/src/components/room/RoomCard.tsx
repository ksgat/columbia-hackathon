'use client'

import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'

interface RoomCardProps {
  room: {
    id: string
    name: string
    description?: string
    member_count: number
    currency_mode: 'coins' | 'clout'
    is_private?: boolean
    created_at: string
  }
}

export function RoomCard({ room }: RoomCardProps) {
  const router = useRouter()

  const getCurrencyIcon = () => {
    return room.currency_mode === 'coins' ? '$' : '*'
  }

  const getCurrencyLabel = () => {
    return room.currency_mode === 'coins' ? 'Coins' : 'Clout'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-dark/50 border border-white/10 rounded-xl p-6 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={() => router.push(`/room/${room.id}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white mb-1">{room.name}</h3>
          {room.description && (
            <p className="text-sm text-white/60 line-clamp-2">{room.description}</p>
          )}
        </div>
        {room.is_private && (
          <div className="ml-2 px-2 py-1 bg-white/10 rounded-md text-xs text-white/60 flex items-center gap-1">
            Private
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6 mt-4 pt-4 border-t border-white/5">
        {/* Member Count */}
        <div className="flex items-center gap-2">
          <span className="text-white/80 font-medium text-sm">
            {room.member_count} {room.member_count === 1 ? 'member' : 'members'}
          </span>
        </div>

        {/* Currency Mode */}
        <div className="flex items-center gap-2">
          <span className="text-white/80 font-medium text-sm">{getCurrencyLabel()}</span>
        </div>
      </div>

      {/* Hover Effect Indicator */}
      <div className="mt-4 flex items-center justify-end">
        <motion.div
          className="text-primary text-sm font-medium flex items-center gap-1"
          initial={{ opacity: 0, x: -5 }}
          whileHover={{ opacity: 1, x: 0 }}
        >
          Enter Room →
        </motion.div>
      </div>
    </motion.div>
  )
}
