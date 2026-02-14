'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { marketApi } from '@/lib/api'

interface Trade {
  id: string
  created_at: string
  outcome: string
  price: number
  shares: number
  cost: number
}

interface PricePoint {
  timestamp: string
  time: string
  yes: number
  no: number
}

type Timeframe = '1H' | '24H' | '7D' | '30D' | 'ALL'

interface PriceHistoryChartProps {
  marketId?: string
  currentYesPrice?: number
  currentNoPrice?: number
  trades?: Trade[]
}

export function PriceHistoryChart({ marketId, currentYesPrice = 0.5, currentNoPrice = 0.5, trades: tradesProp }: PriceHistoryChartProps) {
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([])
  const [allTrades, setAllTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState<Timeframe>('ALL')

  useEffect(() => {
    if (tradesProp !== undefined) {
      setAllTrades(tradesProp)
      buildPriceHistory(tradesProp, timeframe)
    } else if (marketId) {
      loadPriceHistory()
    }
  }, [marketId, tradesProp])

  useEffect(() => {
    // Rebuild when timeframe changes
    buildPriceHistory(allTrades, timeframe)
  }, [timeframe])

  const filterTradesByTimeframe = (trades: Trade[], timeframe: Timeframe): Trade[] => {
    if (timeframe === 'ALL') return trades

    const now = new Date()
    const cutoff = new Date()

    switch (timeframe) {
      case '1H':
        cutoff.setHours(now.getHours() - 1)
        break
      case '24H':
        cutoff.setHours(now.getHours() - 24)
        break
      case '7D':
        cutoff.setDate(now.getDate() - 7)
        break
      case '30D':
        cutoff.setDate(now.getDate() - 30)
        break
    }

    return trades.filter(t => new Date(t.created_at) >= cutoff)
  }

  const buildPriceHistory = (trades: any[], selectedTimeframe: Timeframe = timeframe) => {
    try {
      setLoading(true)

      // Filter trades by timeframe
      const filteredTrades = filterTradesByTimeframe(trades, selectedTimeframe)

      if (!filteredTrades || filteredTrades.length === 0) {
        // No trades yet, show starting point
        const now = new Date()
        const startTime = new Date(now.getTime() - 3600000) // 1 hour ago as default

        setPriceHistory([
          {
            timestamp: startTime.toISOString(),
            time: selectedTimeframe === '1H' || selectedTimeframe === '24H'
              ? startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : startTime.toLocaleDateString([], { month: 'short', day: 'numeric' }),
            yes: 0.5,
            no: 0.5,
          },
          {
            timestamp: now.toISOString(),
            time: selectedTimeframe === '1H' || selectedTimeframe === '24H'
              ? now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : now.toLocaleDateString([], { month: 'short', day: 'numeric' }),
            yes: currentYesPrice,
            no: currentNoPrice,
          },
        ])
        return
      }

      // Build price history from trades
      const points: PricePoint[] = []

      // Calculate total shares for each outcome to get accurate prices
      let totalYesShares = 0
      let totalNoShares = 0

      // Add starting point with actual timestamp
      const startDate = new Date(filteredTrades[0].created_at)
      const startTimeLabel = selectedTimeframe === '1H' || selectedTimeframe === '24H'
        ? startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : startDate.toLocaleDateString([], { month: 'short', day: 'numeric' })

      points.push({
        timestamp: filteredTrades[0].created_at,
        time: startTimeLabel,
        yes: 0.5,
        no: 0.5,
      })

      // Process each trade to update prices
      filteredTrades.forEach((trade, index) => {
        // Update share counts based on trade
        if (trade.outcome === 'yes') {
          totalYesShares += trade.shares
        } else if (trade.outcome === 'no') {
          totalNoShares += trade.shares
        }

        // Calculate new prices based on share distribution
        const total = totalYesShares + totalNoShares
        const newYes = total > 0 ? totalYesShares / total : 0.5
        const newNo = total > 0 ? totalNoShares / total : 0.5

        // Add price point (show every Nth trade to avoid clutter)
        const showInterval = Math.max(1, Math.floor(filteredTrades.length / 30))
        if (index % showInterval === 0 || index === filteredTrades.length - 1) {
          const date = new Date(trade.created_at)
          const timeLabel = selectedTimeframe === '1H' || selectedTimeframe === '24H'
            ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : date.toLocaleDateString([], { month: 'short', day: 'numeric' })

          points.push({
            timestamp: trade.created_at,
            time: timeLabel,
            yes: newYes,
            no: newNo,
          })
        }
      })

      // Add current point with actual timestamp
      const now = new Date()
      const nowTimeLabel = selectedTimeframe === '1H' || selectedTimeframe === '24H'
        ? now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : now.toLocaleDateString([], { month: 'short', day: 'numeric' })

      points.push({
        timestamp: now.toISOString(),
        time: nowTimeLabel,
        yes: currentYesPrice,
        no: currentNoPrice,
      })

      setPriceHistory(points)
    } catch (error) {
      console.error('Failed to build price history:', error)
      // Show default data on error with actual timestamps
      const now = new Date()
      const startTime = new Date(now.getTime() - 3600000) // 1 hour ago

      setPriceHistory([
        {
          timestamp: startTime.toISOString(),
          time: startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          yes: 0.5,
          no: 0.5,
        },
        {
          timestamp: now.toISOString(),
          time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          yes: currentYesPrice,
          no: currentNoPrice,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const loadPriceHistory = async () => {
    if (!marketId) return

    try {
      setLoading(true)
      const response = await marketApi.getTrades(marketId)
      const trades: Trade[] = response.data.trades || response.data
      setAllTrades(trades)
      buildPriceHistory(trades, timeframe)
    } catch (error) {
      console.error('Failed to load price history:', error)
      setAllTrades([])
      buildPriceHistory([], timeframe)
    }
  }

  const timeframes: Timeframe[] = ['1H', '24H', '7D', '30D', 'ALL']

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-muted-foreground">Loading chart...</div>
      </div>
    )
  }

  return (
    <div>
      {/* Timeframe Selector */}
      <div className="flex gap-2 mb-4">
        {timeframes.map((tf) => (
          <button
            key={tf}
            onClick={() => setTimeframe(tf)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
              timeframe === tf
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={priceHistory} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="time"
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px', fontFamily: 'Google Sans, system-ui, sans-serif' }}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
            stroke="hsl(var(--muted-foreground))"
            style={{ fontSize: '12px', fontFamily: 'Google Sans, system-ui, sans-serif' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
              fontSize: '12px',
              fontFamily: 'Google Sans, system-ui, sans-serif',
            }}
            labelStyle={{ color: 'hsl(var(--muted-foreground))', fontFamily: 'Google Sans, system-ui, sans-serif' }}
            formatter={(value: any) => `${(value * 100).toFixed(1)}%`}
          />
          <Legend
            wrapperStyle={{ fontSize: '14px', fontFamily: 'Google Sans, system-ui, sans-serif' }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="yes"
            stroke="#10B981"
            strokeWidth={2}
            dot={false}
            name="YES"
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="no"
            stroke="#EF4444"
            strokeWidth={2}
            dot={false}
            name="NO"
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
