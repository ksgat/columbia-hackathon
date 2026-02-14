"use client"

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { ArrowLeft, TrendingUp } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import * as api from '@/lib/api'

export default function CreateMarketPage() {
  const router = useRouter()
  const params = useParams()
  const roomId = params.id as string
  const { isAuthenticated, isLoading: authLoading } = useAuth()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [expiresInDays, setExpiresInDays] = useState('7')
  const [initialOddsYes, setInitialOddsYes] = useState('50')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!title.trim()) {
      setError('Title is required')
      return
    }

    const oddsYes = parseFloat(initialOddsYes) / 100
    const days = parseInt(expiresInDays)

    if (isNaN(oddsYes) || oddsYes < 0.01 || oddsYes > 0.99) {
      setError('Initial odds must be between 1% and 99%')
      return
    }

    if (isNaN(days) || days < 1) {
      setError('Expiration must be at least 1 day')
      return
    }

    setIsLoading(true)

    try {
      const market = await api.createMarket(roomId, {
        title: title.trim(),
        description: description.trim() || undefined,
        category: category.trim() || undefined,
        initial_odds_yes: oddsYes,
        expires_in_hours: days * 24, // Convert days to hours
      })

      router.push(`/room/${roomId}/market/${market.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to create market')
      setIsLoading(false)
    }
  }

  if (authLoading || !isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-12 px-4 bg-background">
      <div className="max-w-xl mx-auto">
        <Link
          href={`/room/${roomId}`}
          className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground mb-8 transition-colors font-medium text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Room
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6" />
              Create Market
            </CardTitle>
            <CardDescription>
              Create a new prediction market for your room
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title">Question / Title</Label>
                <Input
                  id="title"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Will it snow in NYC this week?"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Make it a yes/no question
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Additional context or resolution criteria..."
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category (Optional)</Label>
                <Input
                  id="category"
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="Sports, Politics, Weather, etc."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="initialOddsYes">
                    Initial Odds (YES %)
                  </Label>
                  <Input
                    id="initialOddsYes"
                    type="number"
                    value={initialOddsYes}
                    onChange={(e) => setInitialOddsYes(e.target.value)}
                    min="1"
                    max="99"
                    step="1"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Default: 50%
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expiresInDays">Expires In (Days)</Label>
                  <Input
                    id="expiresInDays"
                    type="number"
                    value={expiresInDays}
                    onChange={(e) => setExpiresInDays(e.target.value)}
                    min="1"
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    When trading closes
                  </p>
                </div>
              </div>

              {error && (
                <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400 p-3 rounded-md">
                  {error}
                </div>
              )}

              <div className="bg-muted p-4 rounded-lg space-y-2">
                <h3 className="font-semibold text-sm">Preview</h3>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">YES</span>
                    <span className="font-semibold text-green-600">{initialOddsYes}%</span>
                  </div>
                  <div className="w-full bg-background rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{ width: `${initialOddsYes}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">NO</span>
                    <span className="font-semibold text-red-600">{100 - parseFloat(initialOddsYes)}%</span>
                  </div>
                </div>
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={!title.trim() || isLoading}
              >
                {isLoading ? 'Creating...' : 'Create Market'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
