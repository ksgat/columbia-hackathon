'use client'

import { motion } from 'framer-motion'

interface OddsBarProps {
  oddsYes: number
  animated?: boolean
  showLabels?: boolean
}

export function OddsBar({ oddsYes, animated = false, showLabels = true }: OddsBarProps) {
  const yesPercent = Math.round(oddsYes * 100)
  const noPercent = 100 - yesPercent

  const BarComponent = animated ? motion.div : 'div'

  return (
    <div className="space-y-2">
      {showLabels && (
        <div className="flex items-center justify-between text-sm font-medium">
          <span className="text-[#19747E]">YES {yesPercent}%</span>
          <span className="text-gray-600">NO {noPercent}%</span>
        </div>
      )}

      <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
        <BarComponent
          {...(animated
            ? {
                initial: { width: '0%' },
                animate: { width: `${yesPercent}%` },
                transition: { duration: 0.8, ease: 'easeOut' },
              }
            : { style: { width: `${yesPercent}%` } })}
          className="absolute inset-y-0 left-0 bg-[#19747E]"
        />
        <div
          className="absolute inset-y-0 right-0 bg-[#E2E2E2]"
          style={{ width: `${noPercent}%` }}
        />

        {/* Center divider */}
        <div className="absolute inset-y-0 left-1/2 w-px bg-white/20" />
      </div>
    </div>
  )
}
