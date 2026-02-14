'use client'

import { motion } from 'framer-motion'
import { Button } from '@/components/shared/Button'

interface SpectatorBannerProps {
  roomName: string
  onUpgrade: () => void
}

export function SpectatorBanner({ roomName, onUpgrade }: SpectatorBannerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-primary/20 border border-primary/30 rounded-xl p-6 mb-6"
    >
      <div className="flex items-center justify-between gap-6">
        {/* Left side - Info */}
        <div className="flex items-center gap-4">
          <div className="text-4xl">👀</div>
          <div>
            <h3 className="text-lg font-bold text-white mb-1">
              You're viewing as a Spectator
            </h3>
            <p className="text-sm text-white/70">
              Upgrade to Participant to trade in markets, vote on resolutions, and earn clout in{' '}
              <span className="font-semibold text-primary">{roomName}</span>
            </p>
          </div>
        </div>

        {/* Right side - Action */}
        <div className="flex-shrink-0">
          <Button
            variant="primary"
            size="lg"
            onClick={onUpgrade}
            className="whitespace-nowrap shadow-lg shadow-primary/20"
          >
            Upgrade to Participant
          </Button>
        </div>
      </div>

      {/* Benefits List */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2 text-white/80">
            <span className="text-green-500">✓</span>
            <span>Trade in markets</span>
          </div>
          <div className="flex items-center gap-2 text-white/80">
            <span className="text-green-500">✓</span>
            <span>Vote on resolutions</span>
          </div>
          <div className="flex items-center gap-2 text-white/80">
            <span className="text-green-500">✓</span>
            <span>Earn clout & compete</span>
          </div>
        </div>
      </div>

      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-secondary/10 rounded-full blur-3xl -z-10" />
    </motion.div>
  )
}
