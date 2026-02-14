'use client'

import { motion } from 'framer-motion'
import { UserAvatar } from '@/components/shared/UserAvatar'

interface User {
  id: string
  display_name: string
  avatar_url?: string | null
}

interface RivalryStats {
  wins: number
  losses: number
  winRate: number
  totalProfit: number
  lastEncounter: string
}

interface RivalryCardProps {
  user1: User
  user2: User
  user1Stats: RivalryStats
  user2Stats: RivalryStats
  onViewDetails?: () => void
}

export function RivalryCard({
  user1,
  user2,
  user1Stats,
  user2Stats,
  onViewDetails,
}: RivalryCardProps) {
  const totalMatches = user1Stats.wins + user1Stats.losses

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="bg-dark border border-white/10 rounded-xl p-6 cursor-pointer"
      onClick={onViewDetails}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="text-2xl">⚔️</div>
          <div>
            <h3 className="text-sm font-bold text-white">Head to Head</h3>
            <p className="text-xs text-gray-400">{totalMatches} matches</p>
          </div>
        </div>
        <div className="text-xs text-gray-500">
          Last: {new Date(user1Stats.lastEncounter).toLocaleDateString()}
        </div>
      </div>

      {/* Users and Stats */}
      <div className="flex items-center justify-between">
        {/* User 1 */}
        <div className="flex flex-col items-center flex-1">
          <motion.div
            whileHover={{ scale: 1.1 }}
            className="mb-3"
          >
            <UserAvatar user={user1} size="lg" />
          </motion.div>
          <div className="text-sm font-semibold text-white text-center mb-1">
            {user1.display_name}
          </div>
          <div className="text-xs text-gray-400 mb-3">
            {user1Stats.winRate.toFixed(1)}% win rate
          </div>

          {/* Stats */}
          <div className="space-y-2 w-full">
            <div className="bg-white/5 rounded-lg px-3 py-2">
              <div className="text-xs text-gray-400 text-center">Wins</div>
              <div className="text-lg font-bold text-accent text-center">
                {user1Stats.wins}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg px-3 py-2">
              <div className="text-xs text-gray-400 text-center">Profit</div>
              <div className={`text-sm font-bold text-center ${
                user1Stats.totalProfit >= 0 ? 'text-accent' : 'text-red-400'
              }`}>
                ${user1Stats.totalProfit >= 0 ? '+' : ''}{user1Stats.totalProfit.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* VS Divider */}
        <div className="flex flex-col items-center px-6">
          <motion.div
            initial={{ scale: 0, rotate: 0 }}
            animate={{ scale: 1, rotate: 360 }}
            transition={{ duration: 0.8, type: 'spring' }}
            className="w-16 h-16 rounded-full bg-primary flex items-center justify-center mb-2"
          >
            <span className="text-2xl font-bold text-white">VS</span>
          </motion.div>

          {/* Win bar */}
          <div className="w-32 h-3 bg-white/10 rounded-full overflow-hidden mt-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(user1Stats.wins / totalMatches) * 100}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="h-full bg-accent"
            />
          </div>
          <div className="flex justify-between w-32 mt-1">
            <span className="text-xs text-gray-500">{user1Stats.wins}</span>
            <span className="text-xs text-gray-500">{user2Stats.wins}</span>
          </div>
        </div>

        {/* User 2 */}
        <div className="flex flex-col items-center flex-1">
          <motion.div
            whileHover={{ scale: 1.1 }}
            className="mb-3"
          >
            <UserAvatar user={user2} size="lg" />
          </motion.div>
          <div className="text-sm font-semibold text-white text-center mb-1">
            {user2.display_name}
          </div>
          <div className="text-xs text-gray-400 mb-3">
            {user2Stats.winRate.toFixed(1)}% win rate
          </div>

          {/* Stats */}
          <div className="space-y-2 w-full">
            <div className="bg-white/5 rounded-lg px-3 py-2">
              <div className="text-xs text-gray-400 text-center">Wins</div>
              <div className="text-lg font-bold text-accent text-center">
                {user2Stats.wins}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg px-3 py-2">
              <div className="text-xs text-gray-400 text-center">Profit</div>
              <div className={`text-sm font-bold text-center ${
                user2Stats.totalProfit >= 0 ? 'text-accent' : 'text-red-400'
              }`}>
                ${user2Stats.totalProfit >= 0 ? '+' : ''}{user2Stats.totalProfit.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-white/10 text-center">
        <p className="text-xs text-gray-500">
          Click to view detailed rivalry history
        </p>
      </div>
    </motion.div>
  )
}
