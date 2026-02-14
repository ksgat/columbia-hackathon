"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, LogOut, TrendingUp, Users, Sparkles } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import * as api from '@/lib/api'
import { Room } from '@/types/backend'

export default function Home() {
  const router = useRouter()
  const { user, isLoading: authLoading, isAuthenticated, logout } = useAuth()
  const [rooms, setRooms] = useState<Room[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [joinCode, setJoinCode] = useState('')
  const [joiningRoom, setJoiningRoom] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadRooms()
    }
  }, [isAuthenticated])

  const loadRooms = async () => {
    try {
      const data = await api.getRooms()
      setRooms(data)
    } catch (error) {
      console.error('Failed to load rooms:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleJoinRoom = async () => {
    if (!joinCode.trim()) return

    setJoiningRoom(true)
    try {
      await api.joinRoom(joinCode)
      await loadRooms()
      setJoinCode('')
    } catch (error: any) {
      alert(error.message || 'Failed to join room')
    } finally {
      setJoiningRoom(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 px-4 bg-background">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tight mb-2">
              Prophecy
            </h1>
            <p className="text-muted-foreground">
              Welcome back, {user?.display_name}
            </p>
          </div>
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Clout Score</CardDescription>
              <CardTitle className="text-3xl">{user?.clout_score.toFixed(0)}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Rank: <span className="font-semibold">{user?.clout_rank}</span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Win Streak</CardDescription>
              <CardTitle className="text-3xl">{user?.streak_current}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Best: {user?.streak_best}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Virtual Balance</CardDescription>
              <CardTitle className="text-3xl">{user?.balance_virtual.toFixed(0)}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {user?.total_bets_won}/{user?.total_bets_placed} wins
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <Link href="/create">
            <Button size="lg" className="w-full gap-2">
              <Plus className="h-5 w-5" />
              Create New Room
            </Button>
          </Link>

          <div className="flex gap-2">
            <input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="Enter Join Code"
              className="flex h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              maxLength={8}
            />
            <Button
              size="lg"
              variant="outline"
              onClick={handleJoinRoom}
              disabled={!joinCode.trim() || joiningRoom}
            >
              Join
            </Button>
          </div>
        </div>

        {/* Rooms List */}
        <div>
          <h2 className="text-2xl font-bold mb-4">Your Rooms</h2>

          {isLoading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading rooms...
            </div>
          ) : rooms.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Sparkles className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-4">
                  No rooms yet. Create one to get started!
                </p>
                <Link href="/create">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Room
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {rooms.map((room) => (
                <Link key={room.id} href={`/room/${room.id}`}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        {room.name}
                      </CardTitle>
                      {room.description && (
                        <CardDescription>{room.description}</CardDescription>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Join Code:</span>
                          <span className="font-mono font-semibold">{room.join_code}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Mode:</span>
                          <span className="capitalize">{room.currency_mode}</span>
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
