'use client'

import { motion } from 'framer-motion'
import { Button } from '@/components/shared/Button'

interface SuggestedTrade {
  market_id: string
  market_question: string
  action: 'BUY_YES' | 'BUY_NO' | 'SELL_YES' | 'SELL_NO'
  amount: number
  reason: string
}

interface HedgeCardProps {
  summary: string
  suggestedTrades: SuggestedTrade[]
  confidence: number
  onAcceptTrade?: (trade: SuggestedTrade) => void
  onDismiss?: () => void
}

const actionColors = {
  BUY_YES: 'text-accent',
  BUY_NO: 'text-red-400',
  SELL_YES: 'text-orange-400',
  SELL_NO: 'text-blue-400',
}

const actionLabels = {
  BUY_YES: 'Buy YES',
  BUY_NO: 'Buy NO',
  SELL_YES: 'Sell YES',
  SELL_NO: 'Sell NO',
}

export function HedgeCard({
  summary,
  suggestedTrades,
  confidence,
  onAcceptTrade,
  onDismiss,
}: HedgeCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-primary/20 border border-primary/30 rounded-xl p-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-2xl">
            🔮
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Prophet&apos;s Hedge Suggestion</h3>
            <div className="flex items-center gap-2 mt-1">
              <div className="text-xs text-gray-400">Confidence:</div>
              <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden w-24">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${confidence * 100}%` }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                  className="h-full bg-accent"
                />
              </div>
              <div className="text-xs font-semibold text-white">{Math.round(confidence * 100)}%</div>
            </div>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Summary */}
      <div className="bg-white/5 rounded-lg p-4 mb-4">
        <p className="text-sm text-gray-200 leading-relaxed">{summary}</p>
      </div>

      {/* Suggested Trades */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-white/80">Suggested Trades:</h4>
        {suggestedTrades.map((trade, index) => (
          <motion.div
            key={`${trade.market_id}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-darker/50 border border-white/10 rounded-lg p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="text-sm font-medium text-white mb-1">
                  {trade.market_question}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${actionColors[trade.action]}`}>
                    {actionLabels[trade.action]}
                  </span>
                  <span className="text-sm text-gray-400">
                    ${trade.amount.toFixed(2)}
                  </span>
                </div>
              </div>
              {onAcceptTrade && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onAcceptTrade(trade)}
                  className="ml-4"
                >
                  Accept
                </Button>
              )}
            </div>
            <p className="text-xs text-gray-400 italic">{trade.reason}</p>
          </motion.div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <p className="text-xs text-gray-500 italic">
          AI-generated suggestion. Always do your own research before trading.
        </p>
      </div>
    </motion.div>
  )
}
