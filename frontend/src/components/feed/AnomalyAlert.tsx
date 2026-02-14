'use client'

import { motion } from 'framer-motion'

interface AnomalyAlertProps {
  anomaly: {
    id: string
    title: string
    description: string
    severity: 'low' | 'medium' | 'high'
    market_id?: string
    market_title?: string
    detected_at: string
  }
  onClick?: () => void
}

const severityConfig = {
  low: {
    color: 'border-yellow-500/50 bg-yellow-500/10',
    icon: '⚠️',
    textColor: 'text-yellow-500',
    label: 'Low Risk',
  },
  medium: {
    color: 'border-orange-500/50 bg-orange-500/10',
    icon: '⚡',
    textColor: 'text-orange-500',
    label: 'Medium Risk',
  },
  high: {
    color: 'border-red-500/50 bg-red-500/10',
    icon: '🚨',
    textColor: 'text-red-500',
    label: 'High Risk',
  },
}

export function AnomalyAlert({ anomaly, onClick }: AnomalyAlertProps) {
  const config = severityConfig[anomaly.severity]

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const detected = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - detected.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}h ago`
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}d ago`
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`border-2 rounded-xl p-4 ${config.color} ${onClick ? 'cursor-pointer hover:border-opacity-100' : ''} transition-all`}
      onClick={onClick}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="text-3xl flex-shrink-0">
          {config.icon}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className={`text-xs font-bold uppercase tracking-wider ${config.textColor}`}>
              {config.label}
            </span>
            <span className="text-xs text-white/40">{getTimeAgo(anomaly.detected_at)}</span>
          </div>

          {/* Title */}
          <h3 className="text-base font-bold text-white mb-1">{anomaly.title}</h3>

          {/* Description */}
          <p className="text-sm text-white/60 mb-3 line-clamp-2">
            {anomaly.description}
          </p>

          {/* Market Link */}
          {anomaly.market_title && (
            <div className="flex items-center gap-2 text-xs text-white/40">
              <span>📊</span>
              <span className="truncate">{anomaly.market_title}</span>
            </div>
          )}
        </div>
      </div>

      {/* Animation pulse for high severity */}
      {anomaly.severity === 'high' && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-red-500/30"
          animate={{
            opacity: [0.5, 0, 0.5],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      )}
    </motion.div>
  )
}
