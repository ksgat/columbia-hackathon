"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { getMarket, getUserByPhone, createUser, addParticipant } from "@/lib/betting"
import { Market } from "@/types"

export default function InvitePage() {
  const params = useParams()
  const router = useRouter()
  const marketId = params.marketId as string

  const [market, setMarket] = useState<Market | null>(null)
  const [phoneNumber, setPhoneNumber] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if market exists
    const loadedMarket = getMarket(marketId)
    if (!loadedMarket) {
      setError("Market not found")
      return
    }
    setMarket(loadedMarket)

    // Check if user is already authenticated
    const currentUserId = localStorage.getItem('currentUserId')
    if (currentUserId) {
      // User exists, add to market and redirect
      addParticipant(marketId, currentUserId)
      router.push(`/market/${marketId}`)
    }
  }, [marketId, router])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!phoneNumber.trim() || !displayName.trim()) {
      setError("Please fill in all fields")
      return
    }

    setIsLoading(true)

    try {
      // Check if user exists by phone
      let user = getUserByPhone(phoneNumber)
      
      if (!user) {
        // Create new user
        user = createUser(phoneNumber, displayName)
      }

      // Store user ID in localStorage
      localStorage.setItem('currentUserId', user.id)

      // Add user to market participants
      addParticipant(marketId, user.id)

      // Redirect to market
      router.push(`/market/${marketId}`)
    } catch (error: any) {
      setError(error.message || "Failed to join market")
      setIsLoading(false)
    }
  }

  if (error && !market) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <Card className="p-8 max-w-md w-full text-center">
          <p className="text-destructive text-lg">{error}</p>
        </Card>
      </div>
    )
  }

  if (!market) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-background">
      <div className="max-w-sm w-full">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold tracking-tighter mb-2 leading-tight">
            You're Invited!
          </h1>
          <p className="text-base text-muted-foreground font-medium">
            Join <span className="text-foreground font-semibold">{market.groupName}</span>
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Join the Market</CardTitle>
            <CardDescription>
              Enter your details to start betting with your friends
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="+1234567890"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Your Name</Label>
                <Input
                  id="name"
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="John Doe"
                  required
                />
              </div>

              {error && (
                <div className="bg-destructive/10 border border-destructive rounded-md p-3 text-sm text-destructive font-medium">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? "Joining..." : "Join Market"}
              </Button>

              <p className="text-xs text-muted-foreground text-center font-medium">
                You'll start with $100 in play money
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
