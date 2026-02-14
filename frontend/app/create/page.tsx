"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { PhoneInput } from "@/components/phone-input"
import { createMarket, createUser, getUserByPhone } from "@/lib/betting"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function CreateMarket() {
  const router = useRouter()
  const [groupName, setGroupName] = useState("")
  const [phones, setPhones] = useState<string[]>([])
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Check if user is authenticated
  useEffect(() => {
    const userId = localStorage.getItem('currentUserId')
    if (!userId) {
      // Create a default user for demo purposes
      const demoUser = createUser('+15551234567', 'You')
      localStorage.setItem('currentUserId', demoUser.id)
      setCurrentUserId(demoUser.id)
    } else {
      setCurrentUserId(userId)
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!groupName.trim() || !currentUserId) {
      return
    }

    setIsLoading(true)

    try {
      // Create the market
      const market = createMarket(currentUserId, groupName, phones)
      
      // Redirect to the market page
      router.push(`/market/${market.id}`)
    } catch (error) {
      console.error('Error creating market:', error)
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen py-12 px-4 bg-background">
      <div className="max-w-xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-foreground mb-8 transition-colors font-medium text-sm">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>

        <Card>
          <CardHeader>
            <CardTitle>Create a Market</CardTitle>
            <CardDescription>
              Set up a prediction market with your friends
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="groupName">Group Name</Label>
                <Input
                  id="groupName"
                  type="text"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  placeholder="#friend group 1"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label>Add Friends (Optional)</Label>
                <p className="text-xs text-muted-foreground mb-2">
                  Add phone numbers of friends to invite them later
                </p>
                <PhoneInput
                  phones={phones}
                  onChange={setPhones}
                  placeholder="Phone number (e.g., +1234567890)"
                />
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={!groupName.trim() || isLoading}
              >
                {isLoading ? "Creating..." : "Create Market"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
