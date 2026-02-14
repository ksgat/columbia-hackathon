'use client'

import { useState } from 'react'
import { Modal } from '../shared/Modal'
import { Button } from '../shared/Button'
import { marketApi } from '@/lib/api'

interface CreateMarketModalProps {
  isOpen: boolean
  onClose: () => void
  roomId: string
  onSuccess?: () => void
}

export function CreateMarketModal({ isOpen, onClose, roomId, onSuccess }: CreateMarketModalProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('general')
  const [expiresInHours, setExpiresInHours] = useState(24)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!title.trim()) {
      setError('Title is required')
      return
    }

    try {
      setLoading(true)
      setError('')

      const expiresAt = new Date()
      expiresAt.setHours(expiresAt.getHours() + expiresInHours)

      await marketApi.createMarket({
        room_id: roomId,
        title: title.trim(),
        description: description.trim(),
        category,
        expires_at: expiresAt.toISOString(),
        market_type: 'standard',
      })

      // Reset form
      setTitle('')
      setDescription('')
      setCategory('general')
      setExpiresInHours(24)

      onSuccess?.()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create market')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create New Market" maxWidth="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">
            Market Question <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Will it snow tomorrow?"
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            maxLength={200}
          />
          <p className="text-xs text-muted-foreground mt-1">
            {title.length}/200 characters
          </p>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">
            Description (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add context, rules, or clarifications..."
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 min-h-[100px]"
            maxLength={1000}
          />
          <p className="text-xs text-muted-foreground mt-1">
            {description.length}/1000 characters
          </p>
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          >
            <option value="general">General</option>
            <option value="sports">Sports</option>
            <option value="personal">Personal</option>
            <option value="academic">Academic</option>
            <option value="politics">Politics</option>
            <option value="entertainment">Entertainment</option>
            <option value="weather">Weather</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Expires In */}
        <div>
          <label className="block text-sm font-medium mb-2 text-foreground">
            Expires In (Hours)
          </label>
          <input
            type="number"
            value={expiresInHours}
            onChange={(e) => setExpiresInHours(Math.max(1, parseInt(e.target.value) || 1))}
            min="1"
            max="168"
            className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          <p className="text-xs text-muted-foreground mt-1">
            Market will close in {expiresInHours} hours ({Math.floor(expiresInHours / 24)} days)
          </p>
        </div>

        {error && (
          <div className="text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            {error}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={loading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={loading}
            disabled={!title.trim() || loading}
            className="flex-1"
          >
            Create Market
          </Button>
        </div>
      </form>
    </Modal>
  )
}
