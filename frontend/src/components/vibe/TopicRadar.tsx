'use client'

import { motion } from 'framer-motion'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'

interface TopicData {
  category: string
  count: number
  fullMark: number
}

interface TopicRadarProps {
  data: TopicData[]
  title?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: 300,
  md: 400,
  lg: 500,
}

export function TopicRadar({ data, title = 'Market Categories', size = 'md' }: TopicRadarProps) {
  const chartSize = sizeMap[size]

  // Calculate total count for percentage
  const totalCount = data.reduce((sum, item) => sum + item.count, 0)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-darker/50 border border-white/10 rounded-xl p-6"
    >
      {/* Title */}
      <div className="text-center mb-4">
        <h3 className="text-lg font-bold text-white">{title}</h3>
        <p className="text-xs text-gray-400 mt-1">
          Distribution of {totalCount} markets
        </p>
      </div>

      {/* Radar Chart */}
      <div style={{ width: chartSize, height: chartSize }} className="mx-auto">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis
              dataKey="category"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              tickLine={false}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 'dataMax']}
              tick={{ fill: '#6B7280', fontSize: 10 }}
              tickCount={5}
            />
            <Radar
              name="Markets"
              dataKey="count"
              stroke="#8B5CF6"
              fill="#8B5CF6"
              fillOpacity={0.6}
              animationDuration={1000}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-6 grid grid-cols-2 gap-2">
        {data.map((item, index) => {
          const percentage = totalCount > 0 ? ((item.count / totalCount) * 100).toFixed(1) : '0'
          return (
            <motion.div
              key={item.category}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-xs text-gray-300">{item.category}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white">{item.count}</span>
                <span className="text-xs text-gray-500">({percentage}%)</span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </motion.div>
  )
}
