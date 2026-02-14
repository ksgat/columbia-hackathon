'use client'

import { motion } from 'framer-motion'
import { UserAvatar } from '@/components/shared/UserAvatar'

interface LeaderboardRowProps {
  user: {
    display_name: string
    avatar_url?: string | null
  }
  rank: number
  clout: number
  win_rate: number
  isCurrentUser?: boolean
}

export function LeaderboardRow({ user, rank, clout, win_rate, isCurrentUser = false }: LeaderboardRowProps) {
  const getRankDisplay = () => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return `#${rank}`
  }

  const getRankColor = () => {
    if (rank === 1) return 'text-yellow-500'
    if (rank === 2) return 'text-gray-400'
    if (rank === 3) return 'text-amber-700'
    return 'text-white/40'
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-center gap-4 p-4 rounded-lg ${
        isCurrentUser
          ? 'bg-primary/10 border border-primary/30'
          : 'bg-dark/30 border border-white/5 hover:border-white/10'
      } transition-colors`}
    >
      {/* Rank */}
      <div className={`w-12 text-center font-bold text-lg ${getRankColor()}`}>
        {getRankDisplay()}
      </div>

      {/* Avatar */}
      <UserAvatar user={user} size="md" />

      {/* User Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-white font-semibold truncate">{user.display_name}</span>
          {isCurrentUser && (
            <span className="text-xs text-primary font-medium">(You)</span>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6">
        {/* Clout Score */}
        <div className="text-right">
          <div className="text-xs text-white/40 mb-1">Clout</div>
          <div className="text-white font-bold flex items-center gap-1">
            <span className="text-primary">⭐</span>
            <span>{clout.toLocaleString()}</span>
          </div>
        </div>

        {/* Win Rate */}
        <div className="text-right min-w-[80px]">
          <div className="text-xs text-white/40 mb-1">Win Rate</div>
          <div className={`font-bold ${
            win_rate >= 70 ? 'text-green-500' :
            win_rate >= 50 ? 'text-yellow-500' :
            'text-red-500'
          }`}>
            {win_rate.toFixed(1)}%
          </div>
        </div>
      </div>
    </motion.div>
  )
}
