'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Layout } from '@/components/shared/Layout'
import { useAuth } from '@/hooks/useAuth'
import { roomApi, marketApi } from '@/lib/api'
import { useRoomStore } from '@/store/roomStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function HomePage() {
  const router = useRouter()
  const { user, authenticated, isLoading } = useAuth()
  const { rooms, setRooms } = useRoomStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoading && !authenticated) {
      router.push('/')
    }
  }, [authenticated, isLoading, router])

  useEffect(() => {
    if (authenticated) {
      fetchRooms()
    }
  }, [authenticated])

  const fetchRooms = async () => {
    try {
      const { data } = await roomApi.getRooms()
      setRooms(data)
    } catch (error) {
      console.error('Error fetching rooms:', error)
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
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (rooms.length === 0) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-20">
          <Card className="text-center p-8">
            <CardHeader>
              <CardTitle className="text-3xl mb-2">Welcome to Prophecy</CardTitle>
              <CardDescription className="text-lg">
                Create your first room to start making predictions with friends
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-3 gap-6 text-left">
                <div className="space-y-2">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-3">
                    <span className="text-2xl">1</span>
                  </div>
                  <h3 className="font-semibold">Create a Room</h3>
                  <p className="text-sm text-muted-foreground">
                    Set up a private space for your friend group
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-3">
                    <span className="text-2xl">2</span>
                  </div>
                  <h3 className="font-semibold">Make Predictions</h3>
                  <p className="text-sm text-muted-foreground">
                    Bet on anything with virtual or real money
                  </p>
                </div>
                <div className="space-y-2">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-3">
                    <span className="text-2xl">3</span>
                  </div>
                  <h3 className="font-semibold">Win Together</h3>
                  <p className="text-sm text-muted-foreground">
                    Climb the leaderboard and earn bragging rights
                  </p>
                </div>
              </div>
              <Button size="lg" onClick={() => router.push('/rooms/create')}>
                Create Your First Room
              </Button>
            </CardContent>
          </Card>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-1">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back, {user?.display_name}
            </p>
          </div>
          <Button onClick={() => router.push('/rooms/create')}>
            Create Room
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Balance</CardDescription>
              <CardTitle className="text-2xl">{user?.tokens?.toFixed(0) || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Virtual Coins</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Trades</CardDescription>
              <CardTitle className="text-2xl">{user?.total_trades || 0}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">All time</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Win Rate</CardDescription>
              <CardTitle className="text-2xl">
                {user?.total_trades
                  ? Math.round((user.successful_predictions / user.total_trades) * 100)
                  : 0}%
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {user?.successful_predictions || 0} wins
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Active Rooms</CardDescription>
              <CardTitle className="text-2xl">{rooms.length}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Joined</p>
            </CardContent>
          </Card>
        </div>

        {/* Your Rooms */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Your Rooms</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rooms.map((room) => (
              <Card
                key={room.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/room/${room.id}`)}
              >
                <CardHeader>
                  <CardTitle>{room.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {room.description || 'No description'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                      <span className="text-muted-foreground">
                        {room.member_count || 0} members
                      </span>
                      <span className="text-muted-foreground">
                        {room.market_count || 0} markets
                      </span>
                    </div>
                    <span className="text-primary font-medium">View →</span>
                  </div>
                  <div className="mt-3 pt-3 border-t">
                    <span className={`text-xs px-2 py-1 rounded ${
                      room.currency_mode === 'cash'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {room.currency_mode === 'cash' ? 'Real Money' : 'Virtual'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Get started with common tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-start"
                onClick={() => router.push('/rooms/create')}
              >
                <span className="font-semibold mb-1">Create Market</span>
                <span className="text-xs text-muted-foreground">
                  Start a new prediction in a room
                </span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-start"
                onClick={() => rooms[0] && router.push(`/room/${rooms[0].id}`)}
              >
                <span className="font-semibold mb-1">Browse Markets</span>
                <span className="text-xs text-muted-foreground">
                  See active predictions
                </span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex flex-col items-start"
                onClick={() => rooms[0] && router.push(`/room/${rooms[0].id}`)}
              >
                <span className="font-semibold mb-1">Leaderboard</span>
                <span className="text-xs text-muted-foreground">
                  Check your ranking
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  )
}
