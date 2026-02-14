'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Layout } from '@/components/shared/Layout'
import { useAuth } from '@/hooks/useAuth'
import { roomApi, marketApi } from '@/lib/api'
import { MarketCard } from '@/components/market/MarketCard'
import { Button } from '@/components/shared/Button'
import { CreateMarketModal } from '@/components/market/CreateMarketModal'
import { Leaderboard } from '@/components/room/Leaderboard'

export default function RoomPage() {
  const params = useParams()
  const router = useRouter()
  const { authenticated, isLoading } = useAuth()
  const roomId = params.id as string

  const [room, setRoom] = useState<any>(null)
  const [markets, setMarkets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'markets' | 'feed' | 'leaderboard'>('markets')
  const [showCreateMarket, setShowCreateMarket] = useState(false)

  useEffect(() => {
    if (!isLoading && !authenticated) {
      router.push('/')
    }
  }, [authenticated, isLoading, router])

  useEffect(() => {
    if (authenticated && roomId) {
      fetchRoomData()
    }
  }, [authenticated, roomId])

  const fetchRoomData = async () => {
    try {
      setLoading(true)
      const roomRes = await roomApi.getRoom(roomId)
      setRoom(roomRes.data)

      // Fetch markets from the room's feed
      try {
        const feedRes = await roomApi.getFeed(roomId)
        // Extract markets from feed items and map to MarketCard format
        const marketItems = feedRes.data.items?.map((item: any) => ({
          id: item.id,
          title: item.question, // Backend uses 'question' field
          description: item.description,
          odds_yes: item.prices?.yes || 0.5,
          odds_no: item.prices?.no || 0.5,
          total_pool: item.total_volume || 0,
          status: item.status || 'active',
          expires_at: item.close_time,
          created_at: item.created_at
        })) || []
        setMarkets(marketItems)
      } catch (feedError) {
        console.error('Feed error:', feedError)
        setMarkets([])
      }
    } catch (error) {
      console.error('Error fetching room:', error)
      setRoom(null)
    } finally {
      setLoading(false)
    }
  }

  if (isLoading || loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading room...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!room) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-20 text-center">
          <h1 className="text-2xl font-bold mb-4">Room not found</h1>
          <Button onClick={() => router.push('/home')}>Go to Home</Button>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Room Header */}
        <div className="mb-8">
          <button onClick={() => router.push('/home')} className="text-primary hover:underline mb-4">
            ← Back to Home
          </button>
          <h1 className="text-4xl font-bold mb-2">{room.name || 'Unnamed Room'}</h1>
          <p className="text-muted-foreground text-lg mb-4">{room.description || 'No description'}</p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{room.currency_mode === 'cash' ? 'Real Money' : 'Virtual'}</span>
            <span>{room.member_count || 0} members</span>
            {room.min_bet !== undefined && room.max_bet !== undefined && (
              <span>Min: {room.min_bet} | Max: {room.max_bet}</span>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-border">
          {['markets', 'feed', 'leaderboard'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`pb-3 px-2 font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'text-primary border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'markets' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Active Markets</h2>
              <Button onClick={() => setShowCreateMarket(true)}>
                Create Market
              </Button>
            </div>

            {markets.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground mb-4">
                  No markets yet. Be the first to create one!
                </p>
                <Button onClick={() => setShowCreateMarket(true)}>
                  Create First Market
                </Button>
              </div>
            ) : (
              markets.map((market) => market && market.id ? (
                <MarketCard key={market.id} market={market} />
              ) : null)
            )}
          </div>
        )}

        {activeTab === 'feed' && (
          <div className="text-center py-12 text-muted-foreground">
            Feed view coming soon...
          </div>
        )}

        {activeTab === 'leaderboard' && (
          <Leaderboard roomId={roomId} />
        )}

        {/* Create Market Modal */}
        <CreateMarketModal
          isOpen={showCreateMarket}
          onClose={() => setShowCreateMarket(false)}
          roomId={roomId}
          onSuccess={fetchRoomData}
        />
      </div>
    </Layout>
  )
}
