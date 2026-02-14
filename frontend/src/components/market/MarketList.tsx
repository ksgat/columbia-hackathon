'use client'

import { useEffect, useState } from 'react'
import { MarketCard } from './MarketCard'
import { marketApi } from '@/lib/api'

interface MarketListProps {
  roomId?: string
  limit?: number
}

export function MarketList({ roomId, limit }: MarketListProps) {
  const [markets, setMarkets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchMarkets()
  }, [roomId])

  const fetchMarkets = async () => {
    try {
      setLoading(true)
      // This would fetch markets from the backend
      // For now, show empty state
      setMarkets([])
      setError('')
    } catch (err: any) {
      console.error('Error fetching markets:', err)
      setError('Failed to load markets')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading markets...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">{error}</p>
        <button
          onClick={fetchMarkets}
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (markets.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No active markets. Create one to get started!
      </div>
    )
  }

  const displayMarkets = limit ? markets.slice(0, limit) : markets

  return (
    <div className="space-y-4">
      {displayMarkets.map((market) => (
        <MarketCard key={market.id} market={market} />
      ))}
    </div>
  )
}
