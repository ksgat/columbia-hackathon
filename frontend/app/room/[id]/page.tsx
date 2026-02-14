"use client"

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ArrowLeft, Users, Copy, Check, Sparkles, Plus, TrendingUp, Clock, Vote, CheckCircle2, XCircle } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import * as api from '@/lib/api'
import { Room, RoomMember, Market, ProphetBet } from '@/types/backend'

export default function RoomPage() {
  const router = useRouter()
  const params = useParams()
  const roomId = params.id as string
  const { isAuthenticated, isLoading: authLoading } = useAuth()

  const [room, setRoom] = useState<Room | null>(null)
  const [members, setMembers] = useState<RoomMember[]>([])
  const [markets, setMarkets] = useState<Market[]>([])
  const [prophetBets, setProphetBets] = useState<ProphetBet[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generationMessage, setGenerationMessage] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated && roomId) {
      loadRoomData()
    }
  }, [isAuthenticated, roomId])

  const loadRoomData = async () => {
    try {
      const [roomData, membersData, marketsData, prophetBetsData] = await Promise.all([
        api.getRoom(roomId),
        api.getRoomMembers(roomId),
        api.getMarkets(roomId),
        api.getProphetBets(roomId),
      ])

      setRoom(roomData)
      setMembers(membersData)
      setMarkets(marketsData)
      setProphetBets(prophetBetsData)
    } catch (error: any) {
      console.error('Failed to load room:', error)
      if (error.message.includes('not found') || error.message.includes('not a member')) {
        alert('Room not found or you are not a member')
        router.push('/')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const copyJoinCode = () => {
    if (room) {
      navigator.clipboard.writeText(room.join_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleGenerateMarkets = async () => {
    if (!room) return

    setGenerating(true)
    setGenerationMessage('')

    try {
      const response = await api.generateMarketsWithProphet(roomId, 3)
      setGenerationMessage(response.message)

      // Reload markets
      const updatedMarkets = await api.getMarkets(roomId)
      setMarkets(updatedMarkets)
    } catch (error: any) {
      alert(error.message || 'Failed to generate markets')
    } finally {
      setGenerating(false)
    }
  }

  const getStatusBadge = (status: Market['status']) => {
    const badges = {
      pending: { label: 'Pending', color: 'bg-gray-500' },
      active: { label: 'Active', color: 'bg-green-500' },
      voting: { label: 'Voting', color: 'bg-blue-500' },
      disputed: { label: 'Disputed', color: 'bg-orange-500' },
      resolved: { label: 'Resolved', color: 'bg-purple-500' },
      cancelled: { label: 'Cancelled', color: 'bg-red-500' },
    }

    const badge = badges[status] || badges.pending

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium text-white ${badge.color}`}>
        {badge.label}
      </span>
    )
  }

  const getMarketIcon = (type: Market['market_type']) => {
    if (type === 'chained') return <TrendingUp className="h-4 w-4" />
    if (type === 'derivative') return <Sparkles className="h-4 w-4" />
    return null
  }

  if (authLoading || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (!room) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Room not found</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 px-4 bg-background">
      <div className="max-w-6xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground mb-6 transition-colors font-medium text-sm">
          <ArrowLeft className="h-4 w-4" />
          Back to Rooms
        </Link>

        {/* Room Header */}
        <div className="mb-8">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-2">{room.name}</h1>
              {room.description && (
                <p className="text-muted-foreground">{room.description}</p>
              )}
            </div>

            <Card className="md:min-w-[240px]">
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Join Code</p>
                    <div className="flex items-center gap-2">
                      <code className="text-xl font-bold font-mono">{room.join_code}</code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={copyJoinCode}
                      >
                        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Currency Mode</p>
                    <p className="font-semibold capitalize">{room.currency_mode}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Bet Limits</p>
                    <p className="font-semibold">{room.min_bet} - {room.max_bet}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Members */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="h-5 w-5" />
                Members ({members.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {members.map((member) => (
                  <div
                    key={member.user_id}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-muted rounded-full"
                  >
                    <span className="font-medium">{member.display_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {member.role === 'admin' && '👑'}
                      {member.coins_virtual} coins
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Prophet AI Section */}
        <Card className="mb-8 border-purple-500/20 bg-gradient-to-br from-background to-purple-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-purple-500" />
              Prophet AI
            </CardTitle>
            <CardDescription>
              Let Prophet generate prediction markets based on current events
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleGenerateMarkets}
              disabled={generating}
              className="w-full md:w-auto"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {generating ? 'Generating...' : 'Generate Markets'}
            </Button>

            {generationMessage && (
              <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-lg border border-purple-200 dark:border-purple-800">
                <p className="text-sm">{generationMessage}</p>
              </div>
            )}

            {prophetBets.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">Recent Prophet Bets</h3>
                <div className="space-y-2">
                  {prophetBets.slice(0, 5).map((bet) => (
                    <div key={bet.id} className="flex items-start gap-3 p-3 bg-muted rounded-lg text-sm">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`font-semibold ${bet.side === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                            {bet.side.toUpperCase()}
                          </span>
                          <span className="text-muted-foreground">•</span>
                          <span className="text-muted-foreground">{bet.confidence}% confidence</span>
                        </div>
                        <p className="text-muted-foreground">{bet.reasoning}</p>
                      </div>
                      <span className="font-mono font-semibold">{bet.amount}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Markets */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Markets</h2>
            <Link href={`/room/${roomId}/create-market`}>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Market
              </Button>
            </Link>
          </div>

          {markets.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-4">
                  No markets yet. Create one or let Prophet generate some!
                </p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={handleGenerateMarkets} disabled={generating}>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate with Prophet
                  </Button>
                  <Link href={`/room/${roomId}/create-market`}>
                    <Button variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Manually
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {markets.map((market) => (
                <Link key={market.id} href={`/room/${roomId}/market/${market.id}`}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                    <CardHeader>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        {getStatusBadge(market.status)}
                        {getMarketIcon(market.market_type)}
                      </div>
                      <CardTitle className="text-lg line-clamp-2">
                        {market.title}
                      </CardTitle>
                      {market.description && (
                        <CardDescription className="line-clamp-2">
                          {market.description}
                        </CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-muted-foreground">Yes</span>
                          <span className="font-semibold text-green-600">
                            {(market.odds_yes * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full transition-all"
                            style={{ width: `${market.odds_yes * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Pool: {market.total_pool}</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(market.expires_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
