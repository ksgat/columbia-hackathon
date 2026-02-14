'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Logo } from '@/components/shared/Logo'
import { useAuth } from '@/hooks/useAuth'

export default function LoginPage() {
  const router = useRouter()
  const { authenticated, isLoading, login, signup } = useAuth()
  const [isSignup, setIsSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (authenticated && !isLoading) {
      router.push('/home')
    }
  }, [authenticated, isLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isSignup) {
        if (!displayName.trim()) {
          setError('Display name is required')
          setLoading(false)
          return
        }
        await signup(email, password, displayName)
      } else {
        await login(email, password)
      }
      router.push('/home')
    } catch (err: any) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8 flex flex-col items-center">
          <Logo size="xl" />
          <p className="text-muted-foreground mt-4">
            Social prediction markets with friends
          </p>
        </div>

        <Card className="w-full relative">
          <CardHeader>
            <CardTitle>{isSignup ? 'Create your account' : 'Login to your account'}</CardTitle>
            <CardDescription>
              {isSignup
                ? 'Enter your details below to create your account'
                : 'Enter your email below to login to your account'
              }
            </CardDescription>
            <CardAction>
              <Button
                variant="link"
                onClick={() => {
                  setIsSignup(!isSignup)
                  setError('')
                }}
              >
                {isSignup ? 'Login' : 'Sign Up'}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="flex flex-col gap-6">
                {isSignup && (
                  <div className="grid gap-2">
                    <Label htmlFor="displayName">Display Name</Label>
                    <Input
                      id="displayName"
                      type="text"
                      placeholder="John Doe"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      required={isSignup}
                    />
                  </div>
                )}
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="demo@prophecy.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <div className="flex items-center">
                    <Label htmlFor="password">Password</Label>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                {error && (
                  <div className="text-sm text-destructive">
                    {error}
                  </div>
                )}
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex-col gap-2">
            <Button
              type="submit"
              className="w-full"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? 'Please wait...' : (isSignup ? 'Sign Up' : 'Login')}
            </Button>
            <div className="text-xs text-muted-foreground text-center mt-2">
              Dev mode: Use demo@prophecy.com with any password
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
