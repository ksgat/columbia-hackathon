'use client'

import { motion } from 'framer-motion'

interface TickerItem {
  id: string
  title: string
  odds_yes: number
  change: number
}

interface LiveTickerProps {
  items: TickerItem[]
}

export function LiveTicker({ items }: LiveTickerProps) {
  // Duplicate items for seamless infinite scroll
  const duplicatedItems = [...items, ...items]

  const formatOdds = (odds: number) => `${Math.round(odds)}%`

  const getChangeIndicator = (change: number) => {
    if (change > 0) return { symbol: '▲', color: 'text-green-500' }
    if (change < 0) return { symbol: '▼', color: 'text-red-500' }
    return { symbol: '—', color: 'text-white/40' }
  }

  return (
    <div className="bg-darker/90 border-b border-white/10 overflow-hidden py-3">
      <motion.div
        className="flex gap-8 whitespace-nowrap"
        animate={{
          x: [0, '-50%'],
        }}
        transition={{
          duration: 30,
          ease: 'linear',
          repeat: Infinity,
        }}
      >
        {duplicatedItems.map((item, index) => {
          const { symbol, color } = getChangeIndicator(item.change)
          return (
            <div
              key={`${item.id}-${index}`}
              className="flex items-center gap-3 px-4 border-r border-white/10 last:border-r-0"
            >
              <span className="text-white/80 font-medium text-sm">
                {item.title}
              </span>
              <span className="text-primary font-bold text-sm">
                {formatOdds(item.odds_yes)}
              </span>
              <span className={`${color} font-bold text-sm flex items-center gap-1`}>
                {symbol} {Math.abs(item.change).toFixed(1)}%
              </span>
            </div>
          )
        })}
      </motion.div>
    </div>
  )
}
