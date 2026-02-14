import { useState, useEffect } from 'react'
import { marketApi } from '@/lib/api'
import { useSupabaseRealtime } from './useSupabaseRealtime'

export interface Market {
  id: string
  room_id: string
  creator_id: string | null
  title: string
  description: string
  category: string
  market_type: 'standard' | 'whisper' | 'chained' | 'derivative'
  odds_yes: number
  odds_no: number
  total_pool: number
  status: 'pending' | 'active' | 'voting' | 'disputed' | 'resolved' | 'cancelled'
  resolution_result: 'yes' | 'no' | null
  expires_at: string
  created_at: string
}

export function useMarket(marketId: string) {
  const [market, setMarket] = useState<Market | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch initial market data
  useEffect(() => {
    if (!marketId) return

    const fetchMarket = async () => {
      try {
        setLoading(true)
        const { data } = await marketApi.getMarket(marketId)
        setMarket(data)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch market')
      } finally {
        setLoading(false)
      }
    }

    fetchMarket()
  }, [marketId])

  // Subscribe to real-time updates
  useSupabaseRealtime({
    table: 'markets',
    filter: `id=eq.${marketId}`,
    onUpdate: (updated) => {
      setMarket((prev) => (prev ? { ...prev, ...updated } : updated))
    },
  })

  const placeTrade = async (side: 'yes' | 'no', amount: number) => {
    try {
      const { data } = await marketApi.trade(marketId, side, amount)
      // Market will update via real-time subscription
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.message || 'Failed to place trade')
    }
  }

  const castVote = async (vote: 'yes' | 'no') => {
    try {
      const { data } = await marketApi.vote(marketId, vote)
      return data
    } catch (err: any) {
      throw new Error(err.response?.data?.message || 'Failed to cast vote')
    }
  }

  return {
    market,
    loading,
    error,
    placeTrade,
    castVote,
  }
}
