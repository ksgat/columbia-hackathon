'use client'

import { useState } from 'react'
import { Button } from '../shared/Button'

interface TradePanelProps {
  market: {
    id: string
    title: string
    odds_yes: number
    odds_no: number
  }
  userBalance: number
  onTrade: (side: 'yes' | 'no', amount: number) => Promise<any>
}

export function TradePanel({ market, userBalance, onTrade }: TradePanelProps) {
  const [side, setSide] = useState<'yes' | 'no'>('yes')
  const [amount, setAmount] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleTrade = async () => {
    const tradeAmount = parseFloat(amount)
    if (isNaN(tradeAmount) || tradeAmount <= 0) {
      setError('Please enter a valid amount')
      return
    }

    if (tradeAmount > userBalance) {
      setError('Insufficient balance')
      return
    }

    try {
      setLoading(true)
      setError('')
      await onTrade(side, tradeAmount)
      setAmount('')
    } catch (err: any) {
      setError(err.message || 'Failed to place trade')
    } finally {
      setLoading(false)
    }
  }

  const currentOdds = side === 'yes' ? market.odds_yes : market.odds_no
  const estimatedPayout = amount ? (parseFloat(amount) / currentOdds).toFixed(2) : '0'

  return (
    <div className="bg-dark/50 border border-white/10 rounded-xl p-6 space-y-4">
      <h3 className="text-lg font-bold">Place Your Bet</h3>

      {/* Side Selection */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => setSide('yes')}
          className={`py-3 px-4 rounded-lg font-medium transition-all ${
            side === 'yes'
              ? 'bg-[#19747E] text-white'
              : 'bg-white/5 text-white/60 hover:bg-white/10'
          }`}
        >
          <div className="text-sm opacity-60">YES</div>
          <div className="text-lg font-bold">{Math.round(market.odds_yes * 100)}%</div>
        </button>
        <button
          onClick={() => setSide('no')}
          className={`py-3 px-4 rounded-lg font-medium transition-all ${
            side === 'no'
              ? 'bg-[#E2E2E2] text-black'
              : 'bg-white/5 text-white/60 hover:bg-white/10'
          }`}
        >
          <div className="text-sm opacity-60">NO</div>
          <div className="text-lg font-bold">{Math.round(market.odds_no * 100)}%</div>
        </button>
      </div>

      {/* Amount Input */}
      <div>
        <label className="block text-sm text-white/60 mb-2">
          Amount (Balance: {userBalance.toFixed(0)} coins)
        </label>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Enter amount"
          className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30 focus:outline-none focus:border-primary"
        />
      </div>

      {/* Estimated Payout */}
      <div className="bg-white/5 rounded-lg p-3 text-sm">
        <div className="flex justify-between mb-1">
          <span className="text-white/60">Estimated payout if correct:</span>
          <span className="font-bold text-white">{estimatedPayout} coins</span>
        </div>
        <div className="flex justify-between">
          <span className="text-white/60">Potential profit:</span>
          <span className={`font-bold ${parseFloat(estimatedPayout) > parseFloat(amount || '0') ? 'text-[#19747E]' : 'text-gray-400'}`}>
            +{(parseFloat(estimatedPayout) - parseFloat(amount || '0')).toFixed(2)} coins
          </span>
        </div>
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      <Button
        onClick={handleTrade}
        loading={loading}
        disabled={!amount || loading}
        className="w-full"
      >
        Place {side.toUpperCase()} Bet
      </Button>
    </div>
  )
}
