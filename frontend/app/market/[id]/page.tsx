"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PredictionCard } from "@/components/prediction-card"
import { getMarket, getMarketPredictions, getUser, createPrediction } from "@/lib/betting"
import { Market, Prediction, User } from "@/types"
import { Plus, Share2, ArrowLeft, DollarSign } from "lucide-react"

export default function MarketPage() {
  const params = useParams()
  const router = useRouter()
  const marketId = params.id as string

  const [market, setMarket] = useState<Market | null>(null)
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newQuestion, setNewQuestion] = useState("")
  const [shareTooltip, setShareTooltip] = useState(false)

  useEffect(() => {
    loadData()
  }, [marketId])

  const loadData = () => {
    const loadedMarket = getMarket(marketId)
    if (!loadedMarket) {
      router.push('/')
      return
    }
    setMarket(loadedMarket)

    const loadedPredictions = getMarketPredictions(marketId)
    setPredictions(loadedPredictions)

    const userId = localStorage.getItem('currentUserId')
    if (userId) {
      const user = getUser(userId)
      setCurrentUser(user)
    }
  }

  const handleCreatePrediction = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!newQuestion.trim() || !currentUser) return

    try {
      createPrediction(marketId, currentUser.id, newQuestion)
      setNewQuestion("")
      setShowCreateForm(false)
      loadData() // Reload to show new prediction
    } catch (error) {
      console.error('Error creating prediction:', error)
    }
  }

  const handleShare = () => {
    const shareUrl = `${window.location.origin}/invite/${marketId}`
    navigator.clipboard.writeText(shareUrl)
    setShareTooltip(true)
    setTimeout(() => setShareTooltip(false), 2000)
  }

  if (!market) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 px-4 bg-background">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <Link href="/" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors font-medium text-sm">
            <ArrowLeft className="h-4 w-4" />
            Home
          </Link>

          {currentUser && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-muted border text-sm">
              <DollarSign className="h-4 w-4 text-green-600" />
              <span className="font-semibold text-green-600">{currentUser.balance}</span>
            </div>
          )}
        </div>

        {/* Market Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-tighter mb-1">{market.groupName}</h1>
          <p className="text-muted-foreground font-medium text-sm">
            {predictions.length} {predictions.length === 1 ? 'prediction' : 'predictions'}
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-2 mb-8">
          <Button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Create Prediction
          </Button>

          <div className="relative">
            <Button
              variant="outline"
              onClick={handleShare}
              className="gap-1.5"
            >
              <Share2 className="h-4 w-4" />
              Share
            </Button>
            {shareTooltip && (
              <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-foreground text-background text-xs py-1.5 px-3 rounded-md whitespace-nowrap font-medium">
                Link copied!
              </div>
            )}
          </div>
        </div>

        {/* Create Prediction Form */}
        {showCreateForm && (
          <Card className="mb-6 p-5">
            <form onSubmit={handleCreatePrediction} className="space-y-4">
              <div>
                <Label className="mb-2.5">Prediction Question</Label>
                <Input
                  type="text"
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="Will friend x do y?"
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={!newQuestion.trim()}>
                  Create
                </Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Predictions List */}
        <div className="space-y-3">
          {predictions.length === 0 ? (
            <Card className="p-12 text-center">
              <p className="text-muted-foreground mb-5 font-medium">No predictions yet</p>
              <Button
                onClick={() => setShowCreateForm(true)}
                className="gap-1.5"
              >
                <Plus className="h-4 w-4" />
                Create First Prediction
              </Button>
            </Card>
          ) : (
            predictions.map((prediction) => (
              <PredictionCard
                key={prediction.id}
                prediction={prediction}
                marketId={marketId}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
