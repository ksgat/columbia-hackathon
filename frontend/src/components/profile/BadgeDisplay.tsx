'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'

interface Badge {
  id: string
  name: string
  description: string
  icon: string
  earned_at: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}

interface BadgeDisplayProps {
  badges: Badge[]
  maxDisplay?: number
}

const rarityColors = {
  common: 'bg-gray-500',
  rare: 'bg-blue-500',
  epic: 'bg-purple-500',
  legendary: 'bg-amber-500',
}

const rarityBorder = {
  common: 'border-gray-500',
  rare: 'border-blue-500',
  epic: 'border-purple-500',
  legendary: 'border-amber-500',
}

export function BadgeDisplay({ badges, maxDisplay }: BadgeDisplayProps) {
  const [hoveredBadge, setHoveredBadge] = useState<string | null>(null)

  const displayBadges = maxDisplay ? badges.slice(0, maxDisplay) : badges

  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4">
      {displayBadges.map((badge, index) => (
        <motion.div
          key={badge.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          className="relative"
          onMouseEnter={() => setHoveredBadge(badge.id)}
          onMouseLeave={() => setHoveredBadge(null)}
        >
          <motion.div
            whileHover={{ scale: 1.1, rotate: 5 }}
            className={`
              aspect-square rounded-xl border-2 ${rarityBorder[badge.rarity]}
              ${rarityColors[badge.rarity]}
              flex items-center justify-center text-4xl
              cursor-pointer shadow-lg
            `}
          >
            {badge.icon}
          </motion.div>

          {/* Tooltip */}
          {hoveredBadge === badge.id && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-darker border border-white/20 rounded-lg shadow-xl min-w-[200px]"
            >
              <div className="text-sm font-bold text-white mb-1">{badge.name}</div>
              <div className="text-xs text-gray-300 mb-2">{badge.description}</div>
              <div className="text-xs text-gray-400">
                Earned {new Date(badge.earned_at).toLocaleDateString()}
              </div>
              {/* Arrow */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                <div className="border-4 border-transparent border-t-darker" />
              </div>
            </motion.div>
          )}
        </motion.div>
      ))}

      {/* Empty slots if user has fewer badges than grid */}
      {maxDisplay && displayBadges.length < maxDisplay && (
        <>
          {Array.from({ length: maxDisplay - displayBadges.length }).map((_, i) => (
            <div
              key={`empty-${i}`}
              className="aspect-square rounded-xl border-2 border-dashed border-white/10 bg-white/5 flex items-center justify-center"
            >
              <span className="text-2xl text-white/20">?</span>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
