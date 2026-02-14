'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { roomApi } from '@/lib/api'

export default function CreateRoomPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    slug: '',
    is_public: true,
    theme_color: '',
    max_members: 100,
  })

  // Auto-generate slug from name
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')

    setFormData({ ...formData, name, slug })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const { data } = await roomApi.createRoom(formData)
      router.push(`/room/${data.id}`)
    } catch (err: any) {
      // Handle different error formats
      let errorMsg = 'Failed to create room'
      if (err.response?.data) {
        const data = err.response.data
        if (typeof data.detail === 'string') {
          errorMsg = data.detail
        } else if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map((e: any) => e.msg || String(e)).join(', ')
        } else if (typeof data.message === 'string') {
          errorMsg = data.message
        }
      } else if (err.message) {
        errorMsg = err.message
      }
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-2xl mx-auto py-8">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-primary hover:underline mb-4"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold mb-2">Create a Room</h1>
          <p className="text-muted-foreground">
            Set up your prediction market room for your group
          </p>
        </div>

        <Card>
          <form onSubmit={handleSubmit}>
            <CardHeader>
              <CardTitle>Room Details</CardTitle>
              <CardDescription>
                Configure your room settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Room Name</Label>
                <Input
                  id="name"
                  placeholder="My Friend Group"
                  value={formData.name}
                  onChange={handleNameChange}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="slug">Room URL</Label>
                <Input
                  id="slug"
                  placeholder="my-friend-group"
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  This will be your room&apos;s URL: /room/{formData.slug || 'your-room-slug'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  placeholder="A place for friendly predictions"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="maxMembers">Max Members</Label>
                <Input
                  id="maxMembers"
                  type="number"
                  value={formData.max_members}
                  onChange={(e) => setFormData({ ...formData, max_members: parseInt(e.target.value) || 100 })}
                  min="2"
                  max="10000"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum number of members allowed in this room
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="isPublic"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="h-4 w-4 rounded border-input"
                />
                <Label htmlFor="isPublic" className="font-normal cursor-pointer">
                  Make this room public
                </Label>
              </div>

              {error && (
                <div className="text-sm text-destructive">
                  {error}
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button
                type="submit"
                className="w-full"
                disabled={loading || !formData.name}
              >
                {loading ? 'Creating...' : 'Create Room'}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  )
}
