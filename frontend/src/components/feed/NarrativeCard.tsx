'use client'

import { motion } from 'framer-motion'
import { UserAvatar } from '@/components/shared/UserAvatar'

interface NarrativeCardProps {
  narrative: {
    id: string
    title: string
    content: string
    icon?: string
    created_at: string
    related_users?: Array<{
      display_name: string
      avatar_url?: string | null
    }>
  }
}

export function NarrativeCard({ narrative }: NarrativeCardProps) {
  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const created = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - created.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `${diffInHours}h ago`
    const diffInDays = Math.floor(diffInHours / 24)
    return `${diffInDays}d ago`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark/50 border border-white/10 rounded-xl p-6 hover:border-primary/50 transition-colors"
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-2xl flex-shrink-0">
          {narrative.icon || '🔮'}
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-white">{narrative.title}</h3>
            <span className="text-xs text-white/40">{getTimeAgo(narrative.created_at)}</span>
          </div>

          <p className="text-sm text-white/70 leading-relaxed mb-4">
            {narrative.content}
          </p>

          {/* Related Users */}
          {narrative.related_users && narrative.related_users.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-white/40">Related:</span>
              <div className="flex -space-x-2">
                {narrative.related_users.slice(0, 5).map((user, index) => (
                  <div key={index} className="ring-2 ring-dark rounded-full">
                    <UserAvatar user={user} size="sm" />
                  </div>
                ))}
                {narrative.related_users.length > 5 && (
                  <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs text-white/60 ring-2 ring-dark">
                    +{narrative.related_users.length - 5}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Prophet AI Badge */}
      <div className="mt-4 pt-4 border-t border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-primary animate-pulse-slow" />
          <span className="text-xs text-white/40 font-medium">Prophet AI Narrative</span>
        </div>
      </div>
    </motion.div>
  )
}
