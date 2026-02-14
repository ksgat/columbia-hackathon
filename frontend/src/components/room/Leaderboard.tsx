'use client'

import { useEffect, useState } from 'react'
import { UserAvatar } from '../shared/UserAvatar'
import { roomApi } from '@/lib/api'

interface LeaderboardProps {
  roomId: string
}

interface LeaderboardUser {
  id: string
  display_name: string
  avatar_url?: string
  clout_score: number
  clout_rank: string
  total_bets_placed: number
  total_bets_won: number
  streak_current: number
}

export function Leaderboard({ roomId }: LeaderboardProps) {
  const [users, setUsers] = useState<LeaderboardUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchLeaderboard()
  }, [roomId])

  const fetchLeaderboard = async () => {
    try {
      setLoading(true)
      const { data } = await roomApi.getLeaderboard(roomId)
      setUsers(data)
      setError('')
    } catch (err: any) {
      console.error('Error fetching leaderboard:', err)
      setError('Failed to load leaderboard')
      // Set mock data for development
      setUsers([
        {
          id: '1',
          display_name: 'Demo User',
          clout_score: 1200,
          clout_rank: 'Gold',
          total_bets_placed: 25,
          total_bets_won: 18,
          streak_current: 3,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const getRankIcon = (rank: number) => {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return `#${rank}`
  }

  const getWinRate = (user: LeaderboardUser) => {
    if (user.total_bets_placed === 0) return 0
    return Math.round((user.total_bets_won / user.total_bets_placed) * 100)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading leaderboard...</p>
        </div>
      </div>
    )
  }

  if (error && users.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">{error}</p>
        <button
          onClick={fetchLeaderboard}
          className="text-primary hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (users.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No members in this room yet
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-sm text-yellow-600 mb-4">
          Using demo data. Backend not connected yet.
        </div>
      )}

      {users.map((user, index) => {
        const rank = index + 1
        const winRate = getWinRate(user)

        return (
          <div
            key={user.id}
            className="bg-card border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
          >
            <div className="flex items-center gap-4">
              {/* Rank */}
              <div className="text-2xl font-bold w-12 text-center">
                {getRankIcon(rank)}
              </div>

              {/* Avatar */}
              <UserAvatar user={user} size="lg" />

              {/* User Info */}
              <div className="flex-1">
                <div className="font-bold text-lg">{user.display_name}</div>
                <div className="text-sm text-muted-foreground">
                  {user.clout_rank} • {user.clout_score} points
                </div>
              </div>

              {/* Stats */}
              <div className="hidden md:flex gap-6 text-center">
                <div>
                  <div className="text-sm text-muted-foreground">Win Rate</div>
                  <div className={`font-bold ${
                    winRate >= 70 ? 'text-green-600' :
                    winRate >= 50 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {winRate}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Trades</div>
                  <div className="font-bold">{user.total_bets_placed}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Streak</div>
                  <div className="font-bold">
                    {user.streak_current > 0 ? `🔥 ${user.streak_current}` : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile Stats */}
            <div className="md:hidden mt-3 pt-3 border-t border-border flex justify-around text-center text-sm">
              <div>
                <div className="text-muted-foreground">Win Rate</div>
                <div className="font-bold">{winRate}%</div>
              </div>
              <div>
                <div className="text-muted-foreground">Trades</div>
                <div className="font-bold">{user.total_bets_placed}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Streak</div>
                <div className="font-bold">
                  {user.streak_current > 0 ? `${user.streak_current}` : '—'}
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
