"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { getPrediction, getUser, placeBet, calculateOdds, getUserBets } from "@/lib/betting"
import { Prediction, User } from "@/types"
import { ArrowLeft, DollarSign } from "lucide-react"

export default function BettingPage() {
  const params = useParams()
  const router = useRouter()
  const marketId = params.id as string
  const predictionId = params.predId as string

  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [betAmount, setBetAmount] = useState(10)
  const [selectedPosition, setSelectedPosition] = useState<'yes' | 'no' | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasAlreadyBet, setHasAlreadyBet] = useState(false)

  useEffect(() => {
    loadData()
  }, [predictionId])

  const loadData = () => {
    const loadedPrediction = getPrediction(predictionId)
    if (!loadedPrediction) {
      router.push(`/market/${marketId}`)
      return
    }
    setPrediction(loadedPrediction)

    const userId = localStorage.getItem('currentUserId')
    if (userId) {
      const user = getUser(userId)
      setCurrentUser(user)
      
      // Check if user has already bet
      const userBets = getUserBets(userId, predictionId)
      setHasAlreadyBet(userBets.length > 0)
    }
  }

  const handleBetClick = (position: 'yes' | 'no') => {
    setSelectedPosition(position)
    setShowConfirm(true)
    setError(null)
  }

  const handleConfirmBet = () => {
    if (!currentUser || !selectedPosition || !prediction) return

    try {
      placeBet(currentUser.id, predictionId, betAmount, selectedPosition)
      
      // Reload user data
      const updatedUser = getUser(currentUser.id)
      setCurrentUser(updatedUser)
      
      // Reload prediction data
      const updatedPrediction = getPrediction(predictionId)
      setPrediction(updatedPrediction)
      
      // Show success and redirect
      setTimeout(() => {
        router.push(`/market/${marketId}`)
      }, 1000)
    } catch (error: any) {
      setError(error.message)
      setShowConfirm(false)
    }
  }

  const handleCancelBet = () => {
    setShowConfirm(false)
    setSelectedPosition(null)
    setError(null)
  }

  const quickAmounts = [5, 10, 20, 50]

  if (!prediction || !currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  const { yesOdds, noOdds } = calculateOdds(prediction)

  return (
    <div className="min-h-screen py-8 px-4 bg-background">
      <div className="max-w-xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <Link 
            href={`/market/${marketId}`} 
            className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors font-medium text-sm"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Market
          </Link>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-muted border text-sm">
            <DollarSign className="h-4 w-4 text-green-600" />
            <span className="font-semibold text-green-600">{currentUser.balance}</span>
          </div>
        </div>

        {/* Prediction Question */}
        <h1 className="text-3xl font-bold tracking-tighter mb-8 text-center leading-tight">{prediction.question}</h1>

        {/* Current Odds */}
        <Card className="p-5 mb-8">
          <h3 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">Current Odds</h3>
          <div className="flex h-12 rounded-md overflow-hidden mb-3 border">
            <div
              className="bg-green-500/10 border-r border-green-600 flex items-center justify-center font-bold text-green-600 text-base"
              style={{ width: `${yesOdds}%` }}
            >
              {yesOdds}%
            </div>
            <div
              className="bg-red-500/10 border-l border-red-600 flex items-center justify-center font-bold text-red-600 text-base"
              style={{ width: `${noOdds}%` }}
            >
              {noOdds}%
            </div>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground font-semibold">
            <span>YES ${prediction.yesPool}</span>
            <span>Pool ${prediction.yesPool + prediction.noPool}</span>
            <span>NO ${prediction.noPool}</span>
          </div>
        </Card>

        {hasAlreadyBet ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground text-base mb-5 font-medium">You've already placed a bet on this prediction</p>
            <Link href={`/market/${marketId}`}>
              <Button>Back to Market</Button>
            </Link>
          </Card>
        ) : showConfirm ? (
          /* Confirmation Modal */
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-6 text-center tracking-tight">Confirm Your Bet</h2>
            <div className="text-center mb-8">
              <p className="text-muted-foreground mb-2 text-sm font-medium">You're betting</p>
              <p className="text-5xl font-bold tracking-tighter mb-3">
                ${betAmount}
              </p>
              <p className="text-muted-foreground text-sm font-medium">on</p>
              <p className={`text-4xl font-bold tracking-tighter mt-2 ${selectedPosition === 'yes' ? 'text-green-600' : 'text-red-600'}`}>
                {selectedPosition?.toUpperCase()}
              </p>
            </div>

            {error && (
              <div className="bg-destructive/10 border border-destructive rounded-md p-3 mb-6 text-center text-destructive text-sm font-medium">
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="lg"
                className="flex-1"
                onClick={handleCancelBet}
              >
                Cancel
              </Button>
              <Button
                size="lg"
                className={`flex-1 ${selectedPosition === 'yes' ? 'bg-green-600 hover:bg-green-700 active:bg-green-800 text-white' : 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white'}`}
                onClick={handleConfirmBet}
              >
                Confirm
              </Button>
            </div>
          </Card>
        ) : (
          /* Betting Interface */
          <div className="space-y-5">
            {/* Amount Selection */}
            <Card className="p-5">
              <h3 className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">Amount</h3>
              
              {/* Large Amount Display */}
              <div className="mb-4">
                <div className="relative">
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 text-4xl font-bold text-muted-foreground">$</span>
                  <input
                    type="number"
                    min="1"
                    max={currentUser.balance}
                    value={betAmount}
                    onChange={(e) => {
                      const val = Math.min(Math.max(1, Number(e.target.value)), currentUser.balance)
                      setBetAmount(val)
                    }}
                    className="w-full text-5xl font-bold tracking-tighter bg-transparent border-none outline-none pl-8 text-foreground"
                  />
                </div>
              </div>

              {/* Quick Add Buttons */}
              <div className="flex gap-2 mb-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setBetAmount(Math.min(betAmount + 1, currentUser.balance))}
                  className="flex-1 font-semibold"
                >
                  +$1
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setBetAmount(Math.min(betAmount + 20, currentUser.balance))}
                  className="flex-1 font-semibold"
                >
                  +$20
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setBetAmount(Math.min(betAmount + 100, currentUser.balance))}
                  className="flex-1 font-semibold"
                >
                  +$100
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setBetAmount(currentUser.balance)}
                  className="flex-1 font-semibold"
                >
                  Max
                </Button>
              </div>

              <div className="text-xs text-muted-foreground font-semibold">
                Balance: ${currentUser.balance}
              </div>
            </Card>

            {error && (
              <div className="bg-destructive/10 border border-destructive rounded-md p-3 text-center text-destructive text-sm font-medium">
                {error}
              </div>
            )}

            {/* YES/NO Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <Button
                size="lg"
                className="h-28 text-2xl font-bold bg-green-600 hover:bg-green-700 active:bg-green-800 text-white flex-col gap-1 rounded-lg"
                onClick={() => handleBetClick('yes')}
                disabled={betAmount > currentUser.balance || betAmount <= 0}
              >
                <span>YES</span>
                <span className="text-xs font-semibold opacity-90">
                  {yesOdds}% odds
                </span>
              </Button>
              <Button
                size="lg"
                className="h-28 text-2xl font-bold bg-red-600 hover:bg-red-700 active:bg-red-800 text-white flex-col gap-1 rounded-lg"
                onClick={() => handleBetClick('no')}
                disabled={betAmount > currentUser.balance || betAmount <= 0}
              >
                <span>NO</span>
                <span className="text-xs font-semibold opacity-90">
                  {noOdds}% odds
                </span>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
