'use client'

import { motion } from 'framer-motion'
import { useState } from 'react'

interface DayActivity {
  date: string // ISO date string
  count: number
  trades?: number
  volume?: number
}

interface ActivityHeatmapProps {
  activities: DayActivity[]
  weeks?: number // Number of weeks to show, default 12
}

export function ActivityHeatmap({ activities, weeks = 12 }: ActivityHeatmapProps) {
  const [hoveredDay, setHoveredDay] = useState<DayActivity | null>(null)
  const [hoveredPosition, setHoveredPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 })

  // Generate grid data for the last N weeks
  const generateGrid = () => {
    const grid: (DayActivity | null)[][] = []
    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(today.getDate() - weeks * 7)

    // Create a map of activities by date
    const activityMap = new Map<string, DayActivity>()
    activities.forEach(activity => {
      const dateKey = activity.date.split('T')[0]
      activityMap.set(dateKey, activity)
    })

    // Generate grid (7 rows for days of week, N columns for weeks)
    for (let day = 0; day < 7; day++) {
      grid[day] = []
      for (let week = 0; week < weeks; week++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + week * 7 + day)

        if (date > today) {
          grid[day][week] = null
        } else {
          const dateKey = date.toISOString().split('T')[0]
          const activity = activityMap.get(dateKey)
          grid[day][week] = activity || { date: dateKey, count: 0 }
        }
      }
    }

    return grid
  }

  // Get color based on activity count
  const getColor = (count: number) => {
    if (count === 0) return 'bg-white/5'
    if (count < 3) return 'bg-accent/20'
    if (count < 6) return 'bg-accent/40'
    if (count < 9) return 'bg-accent/60'
    if (count < 12) return 'bg-accent/80'
    return 'bg-accent'
  }

  const grid = generateGrid()
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

  // Calculate total activity
  const totalActivity = activities.reduce((sum, act) => sum + act.count, 0)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-darker/50 border border-white/10 rounded-xl p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-white">Trading Activity</h3>
          <p className="text-xs text-gray-400 mt-1">
            {totalActivity} trades in the last {weeks} weeks
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Less</span>
          <div className="flex gap-1">
            <div className="w-3 h-3 rounded-sm bg-white/5" />
            <div className="w-3 h-3 rounded-sm bg-accent/20" />
            <div className="w-3 h-3 rounded-sm bg-accent/40" />
            <div className="w-3 h-3 rounded-sm bg-accent/60" />
            <div className="w-3 h-3 rounded-sm bg-accent" />
          </div>
          <span className="text-xs text-gray-500">More</span>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="overflow-x-auto">
        <div className="inline-flex gap-1">
          {/* Day labels */}
          <div className="flex flex-col gap-1 pr-2">
            <div className="h-3" /> {/* Spacer for month labels */}
            {days.map((day, i) => (
              <div
                key={day}
                className="h-3 flex items-center justify-end text-xs text-gray-500"
                style={{ visibility: i % 2 === 0 ? 'visible' : 'hidden' }}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Grid */}
          <div className="flex flex-col gap-1">
            {/* Month labels */}
            <div className="flex gap-1 h-3 mb-1">
              {grid[0].map((_, weekIndex) => {
                const date = new Date()
                date.setDate(date.getDate() - (weeks - weekIndex - 1) * 7)
                const isFirstOfMonth = date.getDate() <= 7
                return (
                  <div key={weekIndex} className="w-3">
                    {isFirstOfMonth && (
                      <span className="text-xs text-gray-500">
                        {months[date.getMonth()]}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Days */}
            {grid.map((week, dayIndex) => (
              <div key={dayIndex} className="flex gap-1">
                {week.map((day, weekIndex) => {
                  if (!day) return <div key={weekIndex} className="w-3 h-3" />

                  return (
                    <motion.div
                      key={weekIndex}
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: (dayIndex * weeks + weekIndex) * 0.002 }}
                      whileHover={{ scale: 1.5 }}
                      className={`w-3 h-3 rounded-sm cursor-pointer ${getColor(day.count)}`}
                      onMouseEnter={(e) => {
                        setHoveredDay(day)
                        const rect = e.currentTarget.getBoundingClientRect()
                        setHoveredPosition({ x: rect.left, y: rect.top })
                      }}
                      onMouseLeave={() => setHoveredDay(null)}
                    />
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {hoveredDay && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed z-50 bg-darker border border-white/20 rounded-lg shadow-xl px-3 py-2 pointer-events-none"
          style={{
            left: hoveredPosition.x,
            top: hoveredPosition.y - 80,
          }}
        >
          <div className="text-xs font-bold text-white">
            {new Date(hoveredDay.date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            })}
          </div>
          <div className="text-xs text-gray-300 mt-1">
            {hoveredDay.count} {hoveredDay.count === 1 ? 'trade' : 'trades'}
          </div>
          {hoveredDay.volume !== undefined && (
            <div className="text-xs text-gray-400">
              ${hoveredDay.volume.toFixed(2)} volume
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  )
}
