'use client'

import { motion } from 'framer-motion'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'

interface VibeGaugeProps {
  optimismScore: number // 0 to 1
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: 200,
  md: 280,
  lg: 360,
}

export function VibeGauge({ optimismScore, label = 'Room Optimism', size = 'md' }: VibeGaugeProps) {
  // Clamp score between 0 and 1
  const score = Math.max(0, Math.min(1, optimismScore))
  const percentage = Math.round(score * 100)

  // Determine color based on score
  const getColor = (score: number) => {
    if (score < 0.33) return '#EF4444' // red
    if (score < 0.67) return '#F59E0B' // amber
    return '#10B981' // accent green
  }

  const color = getColor(score)

  // Data for radial bar chart
  const data = [
    {
      name: 'optimism',
      value: percentage,
      fill: color,
    },
  ]

  // Determine emoji based on score
  const getEmoji = (score: number) => {
    if (score < 0.2) return '😰'
    if (score < 0.4) return '😟'
    if (score < 0.6) return '😐'
    if (score < 0.8) return '🙂'
    return '😄'
  }

  const chartSize = sizeMap[size]

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: chartSize, height: chartSize * 0.7 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="75%"
            innerRadius="80%"
            outerRadius="100%"
            startAngle={180}
            endAngle={0}
            data={data}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: '#1E293B' }}
              dataKey="value"
              cornerRadius={10}
              animationDuration={1000}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: 'spring' }}
            className="text-5xl mb-2"
          >
            {getEmoji(score)}
          </motion.div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7 }}
            className="text-4xl font-bold text-white"
            style={{ color }}
          >
            {percentage}%
          </motion.div>
        </div>

        {/* Tick marks */}
        <div className="absolute bottom-0 left-0 text-xs text-gray-500 font-medium">0</div>
        <div className="absolute bottom-1/4 left-1/4 text-xs text-gray-500 font-medium">25</div>
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 text-xs text-gray-500 font-medium">50</div>
        <div className="absolute bottom-1/4 right-1/4 text-xs text-gray-500 font-medium">75</div>
        <div className="absolute bottom-0 right-0 text-xs text-gray-500 font-medium">100</div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="text-sm font-medium text-gray-400 mt-2"
      >
        {label}
      </motion.div>
    </div>
  )
}
