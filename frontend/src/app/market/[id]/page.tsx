'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Layout } from '@/components/shared/Layout'
import { useAuth } from '@/hooks/useAuth'
import { marketApi } from '@/lib/api'
import { Button } from '@/components/shared/Button'
import { OddsBar } from '@/components/market/OddsBar'
import { PriceHistoryChart } from '@/components/market/PriceHistoryChart'

export default function MarketPage() {
  const params = useParams()
  const router = useRouter()
  const { authenticated, user, isLoading } = useAuth()
  const marketId = params.id as string

  const [market, setMarket] = useState<any>(null)
  const [trades, setTrades] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [betAmount, setBetAmount] = useState(10)
  const [betSide, setBetSide] = useState<'yes' | 'no'>('yes')
  const [placing, setPlacing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isLoading && !authenticated) {
      router.push('/')
    }
  }, [authenticated, isLoading, router])

  useEffect(() => {
    if (authenticated && marketId) {
      fetchMarketData()
    }
  }, [authenticated, marketId])

  const fetchMarketData = async () => {
    try {
      setLoading(true)
      const [marketRes, tradesRes] = await Promise.all([
        marketApi.getMarket(marketId),
        marketApi.getTrades(marketId, 1).catch(() => ({ data: { trades: [] } }))
      ])
      setMarket(marketRes.data)
      setTrades(tradesRes.data.trades || [])
    } catch (error) {
      console.error('Error fetching market:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePlaceBet = async () => {
    if (!betAmount || betAmount < 1) {
      setError('Bet amount must be at least 1 coin')
      return
    }

    if (user && betAmount > user.tokens) {
      setError('Insufficient balance')
      return
    }

    try {
      setPlacing(true)
      setError('')
      await marketApi.trade(marketId, betSide, betAmount)

      // Refresh market data and user
      await fetchMarketData()
      window.location.reload() // Reload to update user balance

    } catch (err: any) {
      let errorMsg = 'Failed to place bet'
      if (err.response?.data) {
        const data = err.response.data
        if (typeof data.detail === 'string') {
          errorMsg = data.detail
        } else if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map((e: any) => e.msg || String(e)).join(', ')
        }
      }
      setError(errorMsg)
    } finally {
      setPlacing(false)
    }
  }

  if (isLoading || loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading market...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!market) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-20 text-center">
          <h1 className="text-2xl font-bold mb-4">Market not found</h1>
          <Button onClick={() => router.back()}>Go Back</Button>
        </div>
      </Layout>
    )
  }

  const oddsYes = market.prices?.yes || 0.5
  const oddsNo = market.prices?.no || 0.5

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-8">
        <button onClick={() => router.back()} className="text-primary hover:underline mb-6">
          ← Back
        </button>

        {/* Market Header */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h1 className="text-3xl font-bold mb-4">{market.question}</h1>
          {market.description && (
            <p className="text-muted-foreground mb-4">{market.description}</p>
          )}

          <div className="mb-4">
            <OddsBar oddsYes={oddsYes} animated />
          </div>

          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <span className="font-medium">{Math.round(market.total_volume || 0)} coins traded</span>
            <span>Status: <span className="text-foreground capitalize">{market.status}</span></span>
          </div>
        </div>

        {/* Price History Chart */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Price History</h2>
          <PriceHistoryChart
            trades={trades}
            currentYesPrice={oddsYes}
            currentNoPrice={oddsNo}
          />
        </div>

        {/* Trading Section */}
        {market.status === 'open' && (
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">Place Your Bet</h2>

            {/* Side Selection */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <button
                onClick={() => setBetSide('yes')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  betSide === 'yes'
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="text-2xl font-bold mb-2">YES</div>
                <div className="text-sm text-muted-foreground">
                  {Math.round(oddsYes * 100)}% chance
                </div>
              </button>

              <button
                onClick={() => setBetSide('no')}
                className={`p-4 rounded-lg border-2 transition-all ${
                  betSide === 'no'
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="text-2xl font-bold mb-2">NO</div>
                <div className="text-sm text-muted-foreground">
                  {Math.round(oddsNo * 100)}% chance
                </div>
              </button>
            </div>

            {/* Amount Input */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Bet Amount (coins)
              </label>
              <input
                type="number"
                value={betAmount}
                onChange={(e) => setBetAmount(parseInt(e.target.value) || 0)}
                min="1"
                max={user?.tokens || 1000}
                className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Your balance: {Math.round(user?.tokens || 0)} coins
              </p>
            </div>

            {error && (
              <div className="mb-4 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                {error}
              </div>
            )}

            <Button
              onClick={handlePlaceBet}
              disabled={placing || betAmount < 1 || !user || betAmount > user.tokens}
              className="w-full"
            >
              {placing ? 'Placing Bet...' : `Bet ${betAmount} coins on ${betSide.toUpperCase()}`}
            </Button>
          </div>
        )}

        {/* Recent Trades */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-xl font-bold mb-4">Recent Trades</h2>

          {trades.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No trades yet. Be the first!
            </div>
          ) : (
            <div className="space-y-2">
              {trades.slice(0, 10).map((trade) => (
                <div
                  key={trade.id}
                  className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
                >
                  <div>
                    <span className={`font-medium ${
                      trade.outcome === 'yes' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {trade.outcome.toUpperCase()}
                    </span>
                    <span className="text-muted-foreground text-sm ml-2">
                      {Math.round(trade.shares)} shares @ {Math.round(trade.price * 100)}%
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{Math.round(trade.cost)} coins</div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(trade.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
