'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Layout } from '@/components/shared/Layout'
import { useAuth } from '@/hooks/useAuth'
import { roomApi } from '@/lib/api'
import { Button } from '@/components/shared/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

function JoinForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { authenticated, isLoading } = useAuth()
  const [joinCode, setJoinCode] = useState('')
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isLoading && !authenticated) {
      router.push('/')
    }
  }, [authenticated, isLoading, router])

  useEffect(() => {
    // Auto-fill join code from URL
    const code = searchParams.get('code')
    if (code) {
      setJoinCode(code)
    }
  }, [searchParams])

  const handleJoin = async () => {
    if (!joinCode) {
      setError('Please enter a join code')
      return
    }

    try {
      setJoining(true)
      setError('')
      const response = await roomApi.joinByCode(joinCode)
      const roomId = response.data.room.id
      router.push(`/room/${roomId}`)
    } catch (err: any) {
      console.error('Error joining room:', err)
      const errorMsg = err.response?.data?.detail || 'Failed to join room'
      setError(errorMsg)
    } finally {
      setJoining(false)
    }
  }

  if (isLoading) {
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

  return (
    <Layout>
      <div className="max-w-md mx-auto px-4 py-20">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Join a Room</CardTitle>
            <CardDescription>
              Enter a join code or use an invite link to join a prediction room
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Join Code
              </label>
              <input
                type="text"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="Enter code (e.g., ABC12345)"
                className="w-full px-4 py-3 border border-border rounded-lg font-mono text-lg tracking-wider uppercase focus:outline-none focus:ring-2 focus:ring-primary"
                maxLength={8}
              />
            </div>

            {error && (
              <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                {error}
              </div>
            )}

            <Button
              onClick={handleJoin}
              disabled={joining || !joinCode}
              className="w-full"
            >
              {joining ? 'Joining...' : 'Join Room'}
            </Button>

            <div className="pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => router.push('/home')}
                className="w-full"
              >
                Back to Home
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>Don&apos;t have a join code?</p>
          <button
            onClick={() => router.push('/home')}
            className="text-primary hover:underline mt-1"
          >
            Browse public rooms
          </button>
        </div>
      </div>
    </Layout>
  )
}

export default function JoinPage() {
  return (
    <Suspense fallback={
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading...</p>
          </div>
        </div>
      </Layout>
    }>
      <JoinForm />
    </Suspense>
  )
}
