"use client"

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ArrowLeft, TrendingUp, Clock, Users, Sparkles, Vote, CheckCircle2, XCircle, BarChart3 } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import * as api from '@/lib/api'
import { Market, Trade, Position, VoteSummary, ProphetBet } from '@/types/backend'

export default function MarketDetailPage() {
  const router = useRouter()
  const params = useParams()
  const roomId = params.id as string
  const marketId = params.marketId as string
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()

  const [market, setMarket] = useState<Market | null>(null)
  const [position, setPosition] = useState<Position | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [voteSummary, setVoteSummary] = useState<VoteSummary | null>(null)
  const [prophetBet, setProphetBet] = useState<ProphetBet | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Trading state
  const [tradeSide, setTradeSide] = useState<'yes' | 'no'>('yes')
  const [tradeAmount, setTradeAmount] = useState('')
  const [isTrading, setIsTrading] = useState(false)
  const [tradePreview, setTradePreview] = useState<{ shares: number; newOdds: number } | null>(null)

  // Voting state
  const [isVoting, setIsVoting] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated && marketId) {
      loadMarketData()
    }
  }, [isAuthenticated, marketId])

  useEffect(() => {
    if (market && tradeAmount && parseFloat(tradeAmount) > 0) {
      calculateTradePreview()
    } else {
      setTradePreview(null)
    }
  }, [tradeAmount, tradeSide, market])

  const loadMarketData = async () => {
    try {
      const [marketData, positionData, tradesData] = await Promise.all([
        api.getMarket(marketId),
        api.getPosition(marketId).catch(() => null),
        api.getTrades(marketId),
      ])

      setMarket(marketData)
      setPosition(positionData)
      setTrades(tradesData)

      // Load voting data if in voting status
      if (marketData.status === 'voting') {
        const votes = await api.getVotes(marketId)
        setVoteSummary(votes)
      }

      // Load Prophet bet
      try {
        const prophetBets = await api.getProphetBets(roomId)
        const marketProphetBet = prophetBets.find(bet => bet.market_id === marketId)
        if (marketProphetBet) {
          setProphetBet(marketProphetBet)
        }
      } catch (error) {
        console.error('Failed to load Prophet bet:', error)
      }
    } catch (error: any) {
      console.error('Failed to load market:', error)
      alert('Failed to load market')
      router.push(`/room/${roomId}`)
    } finally {
      setIsLoading(false)
    }
  }

  const calculateTradePreview = async () => {
    if (!market || !tradeAmount) return

    const amount = parseFloat(tradeAmount)
    if (isNaN(amount) || amount <= 0) {
      setTradePreview(null)
      return
    }

    try {
      const preview = await api.previewTrade(marketId, {
        side: tradeSide,
        amount,
      })
      setTradePreview({
        shares: preview.shares_received,
        newOdds: tradeSide === 'yes' ? preview.new_odds_yes : preview.new_odds_no,
      })
    } catch (error) {
      console.error('Failed to preview trade:', error)
      setTradePreview(null)
    }
  }

  const handleTrade = async () => {
    if (!market || !tradeAmount) return

    const amount = parseFloat(tradeAmount)
    if (isNaN(amount) || amount <= 0) {
      alert('Invalid amount')
      return
    }

    setIsTrading(true)

    try {
      await api.placeTrade(marketId, {
        side: tradeSide,
        amount,
      })

      // Reload market data
      await loadMarketData()
      setTradeAmount('')
      setTradePreview(null)
    } catch (error: any) {
      alert(error.message || 'Trade failed')
    } finally {
      setIsTrading(false)
    }
  }

  const handleVote = async (vote: 'yes' | 'no') => {
    if (!market) return

    setIsVoting(true)

    try {
      await api.submitVote(marketId, vote)

      // Reload voting data
      const votes = await api.getVotes(marketId)
      setVoteSummary(votes)
    } catch (error: any) {
      alert(error.message || 'Vote failed')
    } finally {
      setIsVoting(false)
    }
  }

  const getStatusBadge = (status: Market['status']) => {
    const badges = {
      pending: { label: 'Pending', color: 'bg-gray-500', icon: Clock },
      active: { label: 'Active', color: 'bg-green-500', icon: TrendingUp },
      voting: { label: 'Voting', color: 'bg-blue-500', icon: Vote },
      disputed: { label: 'Disputed', color: 'bg-orange-500', icon: XCircle },
      resolved: { label: 'Resolved', color: 'bg-purple-500', icon: CheckCircle2 },
      cancelled: { label: 'Cancelled', color: 'bg-red-500', icon: XCircle },
    }

    const badge = badges[status] || badges.pending
    const Icon = badge.icon

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium text-white ${badge.color}`}>
        <Icon className="h-4 w-4" />
        {badge.label}
      </span>
    )
  }

  if (authLoading || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!market) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Market not found</div>
      </div>
    )
  }

  const canTrade = market.status === 'active'
  const canVote = market.status === 'voting'
  const isResolved = market.status === 'resolved'

  return (
    <div className="min-h-screen py-8 px-4 bg-background">
      <div className="max-w-6xl mx-auto">
        <Link
          href={`/room/${roomId}`}
          className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground mb-6 transition-colors font-medium text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Room
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Market Header */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4 mb-4">
                  {getStatusBadge(market.status)}
                  {market.market_type !== 'standard' && (
                    <span className="text-xs px-2 py-1 bg-muted rounded-full capitalize">
                      {market.market_type}
                    </span>
                  )}
                </div>
                <CardTitle className="text-2xl">{market.title}</CardTitle>
                {market.description && (
                  <CardDescription className="text-base mt-2">
                    {market.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">Total Pool</p>
                    <p className="text-xl font-bold">{market.total_pool.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Expires</p>
                    <p className="font-semibold flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {new Date(market.expires_at).toLocaleString()}
                    </p>
                  </div>
                  {market.category && (
                    <div>
                      <p className="text-muted-foreground mb-1">Category</p>
                      <p className="font-semibold">{market.category}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-muted-foreground mb-1">Currency</p>
                    <p className="font-semibold capitalize">{market.currency_mode}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Current Odds */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Current Odds</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold">YES</span>
                    <span className="text-2xl font-bold text-green-600">
                      {(market.odds_yes * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div
                      className="bg-green-600 h-3 rounded-full transition-all"
                      style={{ width: `${market.odds_yes * 100}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {(market.total_yes_shares || 0).toFixed(0)} shares
                  </p>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold">NO</span>
                    <span className="text-2xl font-bold text-red-600">
                      {((market.odds_no || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div
                      className="bg-red-600 h-3 rounded-full transition-all"
                      style={{ width: `${(market.odds_no || 0) * 100}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {(market.total_no_shares || 0).toFixed(0)} shares
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Prophet Bet */}
            {prophetBet && (
              <Card className="border-purple-500/20 bg-gradient-to-br from-background to-purple-500/5">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-500" />
                    Prophet's Prediction
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold">Bet:</span>
                      <span className={`text-lg font-bold ${prophetBet.side === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                        {prophetBet.side.toUpperCase()} ({prophetBet.confidence}% confidence)
                      </span>
                    </div>
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-sm">{prophetBet.reasoning}</p>
                    </div>
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>Amount: {prophetBet.amount}</span>
                      <span>Shares: {prophetBet.shares_received.toFixed(2)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Voting Interface */}
            {canVote && voteSummary && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Vote className="h-5 w-5" />
                    Community Resolution Vote
                  </CardTitle>
                  <CardDescription>
                    Vote on how this market should resolve. 3/4 supermajority required.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Button
                      size="lg"
                      variant={voteSummary.user_vote === 'yes' ? 'default' : 'outline'}
                      onClick={() => handleVote('yes')}
                      disabled={isVoting}
                      className="h-20"
                    >
                      <div className="text-center">
                        <div className="text-2xl font-bold">YES</div>
                        <div className="text-sm opacity-80">{voteSummary.yes_votes} votes</div>
                      </div>
                    </Button>
                    <Button
                      size="lg"
                      variant={voteSummary.user_vote === 'no' ? 'default' : 'outline'}
                      onClick={() => handleVote('no')}
                      disabled={isVoting}
                      className="h-20"
                    >
                      <div className="text-center">
                        <div className="text-2xl font-bold">NO</div>
                        <div className="text-sm opacity-80">{voteSummary.no_votes} votes</div>
                      </div>
                    </Button>
                  </div>
                  <div className="text-sm text-muted-foreground text-center">
                    Total votes: {voteSummary.total_votes}
                    {voteSummary.user_vote && (
                      <span className="ml-2 font-semibold">
                        (You voted {voteSummary.user_vote.toUpperCase()})
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Resolution Result */}
            {isResolved && market.resolution_result && (
              <Card className={market.resolution_result === 'yes' ? 'border-green-500/20' : 'border-red-500/20'}>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5" />
                    Market Resolved
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-4">
                    <div className={`text-4xl font-bold mb-2 ${market.resolution_result === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                      {market.resolution_result.toUpperCase()}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Resolved via {market.resolution_method}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Recent Trades */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Recent Trades
                </CardTitle>
              </CardHeader>
              <CardContent>
                {trades.length === 0 ? (
                  <p className="text-center text-muted-foreground py-4">No trades yet</p>
                ) : (
                  <div className="space-y-2">
                    {trades.slice(0, 10).map((trade) => (
                      <div key={trade.id} className="flex items-center justify-between p-2 bg-muted rounded-lg text-sm">
                        <div className="flex items-center gap-3">
                          <span className={`font-semibold ${trade.side === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                            {trade.side.toUpperCase()}
                          </span>
                          {trade.is_prophet_trade && (
                            <span className="text-xs px-2 py-0.5 bg-purple-500/20 text-purple-600 rounded-full flex items-center gap-1">
                              <Sparkles className="h-3 w-3" />
                              Prophet
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="font-mono">{trade.amount}</span>
                          <span className="text-muted-foreground">→</span>
                          <span className="font-mono">{trade.shares_received.toFixed(2)} shares</span>
                          <span className="text-muted-foreground text-xs">
                            @{(trade.odds_at_trade * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Your Position */}
            {position && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Your Position</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Side</p>
                    <p className={`text-xl font-bold ${position.side === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                      {position.side.toUpperCase()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Shares</p>
                    <p className="font-semibold">{position.total_shares.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Invested</p>
                    <p className="font-semibold">{position.total_invested.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Current Value</p>
                    <p className="font-semibold">{position.current_value.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">P&L</p>
                    <p className={`text-xl font-bold ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl.toFixed(0)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trading Interface */}
            {canTrade && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Place Trade</CardTitle>
                  <CardDescription>
                    Buy shares using LMSR pricing
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Side</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant={tradeSide === 'yes' ? 'default' : 'outline'}
                        onClick={() => setTradeSide('yes')}
                        className="h-12"
                      >
                        <div className="text-center">
                          <div className="font-bold">YES</div>
                          <div className="text-xs opacity-80">{(market.odds_yes * 100).toFixed(1)}%</div>
                        </div>
                      </Button>
                      <Button
                        variant={tradeSide === 'no' ? 'default' : 'outline'}
                        onClick={() => setTradeSide('no')}
                        className="h-12"
                      >
                        <div className="text-center">
                          <div className="font-bold">NO</div>
                          <div className="text-xs opacity-80">{(market.odds_no * 100).toFixed(1)}%</div>
                        </div>
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="amount">Amount</Label>
                    <Input
                      id="amount"
                      type="number"
                      value={tradeAmount}
                      onChange={(e) => setTradeAmount(e.target.value)}
                      placeholder="Enter amount"
                      min="1"
                    />
                  </div>

                  {tradePreview && (
                    <div className="p-3 bg-muted rounded-lg space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">You'll receive:</span>
                        <span className="font-semibold">{tradePreview.shares.toFixed(2)} shares</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">New odds:</span>
                        <span className="font-semibold">{(tradePreview.newOdds * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  )}

                  <Button
                    onClick={handleTrade}
                    disabled={!tradeAmount || isTrading || !tradePreview}
                    className="w-full"
                    size="lg"
                  >
                    {isTrading ? 'Trading...' : `Buy ${tradeSide.toUpperCase()}`}
                  </Button>

                  <p className="text-xs text-muted-foreground text-center">
                    Your balance: {user?.balance_virtual.toFixed(0)}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
