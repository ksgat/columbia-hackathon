'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/shared/Button'

interface WhisperFormProps {
  roomId: string
  onSubmit: (data: { title: string; description: string }) => Promise<void>
  onCancel?: () => void
}

export function WhisperForm({ roomId, onSubmit, onCancel }: WhisperFormProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError('Please enter a market title')
      return
    }

    if (!description.trim()) {
      setError('Please enter a description')
      return
    }

    setLoading(true)
    try {
      await onSubmit({ title: title.trim(), description: description.trim() })
      setTitle('')
      setDescription('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit whisper')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark/50 border border-white/10 rounded-xl p-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">🤫</span>
        <div>
          <h3 className="text-lg font-bold text-white">Anonymous Market Whisper</h3>
          <p className="text-sm text-white/60">
            Suggest a market idea anonymously to the room
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title Input */}
        <div>
          <label htmlFor="whisper-title" className="block text-sm font-medium text-white/80 mb-2">
            Market Title
          </label>
          <input
            id="whisper-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Will it snow this weekend?"
            maxLength={200}
            className="w-full px-4 py-3 bg-darker/50 border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-primary/50 transition-colors"
            disabled={loading}
          />
          <div className="mt-1 text-xs text-white/40 text-right">
            {title.length}/200
          </div>
        </div>

        {/* Description Input */}
        <div>
          <label htmlFor="whisper-description" className="block text-sm font-medium text-white/80 mb-2">
            Description
          </label>
          <textarea
            id="whisper-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Provide details about the market, resolution criteria, etc."
            rows={4}
            maxLength={1000}
            className="w-full px-4 py-3 bg-darker/50 border border-white/10 rounded-lg text-white placeholder:text-white/30 focus:outline-none focus:border-primary/50 transition-colors resize-none"
            disabled={loading}
          />
          <div className="mt-1 text-xs text-white/40 text-right">
            {description.length}/1000
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-500"
          >
            {error}
          </motion.div>
        )}

        {/* Info Box */}
        <div className="bg-primary/10 border border-primary/20 rounded-lg p-3 text-sm text-white/70">
          <div className="flex items-start gap-2">
            <span className="text-primary mt-0.5">ℹ️</span>
            <p>
              Your suggestion will be submitted anonymously. Room moderators will review it before
              creating the market.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            className="flex-1"
            loading={loading}
          >
            Submit Whisper
          </Button>
          {onCancel && (
            <Button
              type="button"
              variant="ghost"
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </Button>
          )}
        </div>
      </form>
    </motion.div>
  )
}
