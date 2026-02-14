"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { ArrowLeft, Coins } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import * as api from "@/lib/api"

export default function CreateRoom() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [currencyMode, setCurrencyMode] = useState<'virtual' | 'cash' | 'both'>('virtual')
  const [minBet, setMinBet] = useState('10')
  const [maxBet, setMaxBet] = useState('1000')
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

    if (!name.trim()) {
      setError('Room name is required')
      return
    }

    const minBetNum = parseInt(minBet)
    const maxBetNum = parseInt(maxBet)

    if (isNaN(minBetNum) || isNaN(maxBetNum)) {
      setError('Bet limits must be valid numbers')
      return
    }

    if (minBetNum < 1) {
      setError('Minimum bet must be at least 1')
      return
    }

    if (maxBetNum < minBetNum) {
      setError('Maximum bet must be greater than minimum bet')
      return
    }

    setIsLoading(true)

    try {
      const room = await api.createRoom({
        name: name.trim(),
        description: description.trim() || undefined,
        currency_mode: currencyMode,
        min_bet: minBetNum,
        max_bet: maxBetNum,
      })

      router.push(`/room/${room.id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to create room')
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
        <Link href="/" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground mb-8 transition-colors font-medium text-sm">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Coins className="h-6 w-6" />
              Create a Room
            </CardTitle>
            <CardDescription>
              Set up a prediction market room for your group
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Room Name</Label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Friend Group Predictions"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (Optional)</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What will this room be used for?"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="currencyMode">Currency Mode</Label>
                <select
                  id="currencyMode"
                  value={currencyMode}
                  onChange={(e) => setCurrencyMode(e.target.value as 'virtual' | 'cash' | 'both')}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="virtual">Virtual (Fun money)</option>
                  <option value="cash">Cash (Real stakes)</option>
                  <option value="both">Both</option>
                </select>
                <p className="text-xs text-muted-foreground">
                  Virtual mode uses play money, cash mode uses real stakes
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="minBet">Minimum Bet</Label>
                  <Input
                    id="minBet"
                    type="number"
                    value={minBet}
                    onChange={(e) => setMinBet(e.target.value)}
                    min="1"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxBet">Maximum Bet</Label>
                  <Input
                    id="maxBet"
                    type="number"
                    value={maxBet}
                    onChange={(e) => setMaxBet(e.target.value)}
                    min="1"
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="text-sm text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400 p-3 rounded-md">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={!name.trim() || isLoading}
              >
                {isLoading ? "Creating..." : "Create Room"}
              </Button>

              <p className="text-xs text-muted-foreground text-center">
                A unique join code will be generated for your room
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
