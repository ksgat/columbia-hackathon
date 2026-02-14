'use client'

import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { OddsBar } from './OddsBar'
import { Button } from '../shared/Button'

interface MarketCardProps {
  market: {
    id: string
    title: string
    description?: string
    odds_yes: number
    odds_no: number
    total_pool: number
    status: string
    expires_at: string
    created_at: string
  }
  compact?: boolean
  onBet?: (side: 'yes' | 'no') => void
}

export function MarketCard({ market, compact = false, onBet }: MarketCardProps) {
  const router = useRouter()

  const getTimeRemaining = () => {
    const now = new Date()
    const expires = new Date(market.expires_at)
    const diff = expires.getTime() - now.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    return hours > 0 ? `${hours}h` : 'Expired'
  }

  const getStatusBadge = () => {
    const badges = {
      active: { label: 'ACTIVE', color: 'bg-[#19747E] text-white' },
      voting: { label: 'VOTING', color: 'bg-[#19747E] text-white' },
      resolved: { label: 'RESOLVED', color: 'bg-[#19747E] text-white' },
      disputed: { label: 'DISPUTED', color: 'bg-[#E2E2E2] text-black' },
      cancelled: { label: 'CANCELLED', color: 'bg-[#E2E2E2] text-black' },
      pending: { label: 'PENDING', color: 'bg-[#E2E2E2] text-black' },
    }
    const badge = badges[market.status as keyof typeof badges] || badges.active
    return (
      <span className={`${badge.color} text-xs px-2 py-1 rounded-full font-medium`}>
        {badge.label}
      </span>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card border border-border rounded-xl p-6 hover:border-primary/50 transition-colors cursor-pointer"
      onClick={() => router.push(`/market/${market.id}`)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold mb-2">{market.title || 'Untitled Market'}</h3>
          {!compact && market.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">{market.description}</p>
          )}
        </div>
        {getStatusBadge()}
      </div>

      <OddsBar oddsYes={market.odds_yes || 0.5} animated />

      <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
        <div className="flex items-center gap-4">
          <span>{market.total_pool ? Math.round(market.total_pool) : 0} coins</span>
          <span>{market.expires_at ? getTimeRemaining() : 'No expiry'}</span>
        </div>
      </div>

      {market.status === 'active' && onBet && (
        <div className="flex gap-2 mt-4" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onBet('yes')}
            className="flex-1"
          >
            Bet YES
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onBet('no')}
            className="flex-1"
          >
            Bet NO
          </Button>
        </div>
      )}

      {market.status === 'voting' && (
        <div className="mt-4 text-center text-sm text-[#19747E]">
          Resolution voting in progress
        </div>
      )}
    </motion.div>
  )
}
