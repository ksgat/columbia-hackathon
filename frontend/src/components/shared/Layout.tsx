'use client'

import { ReactNode } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { UserAvatar } from './UserAvatar'
import { Button } from './Button'
import { Logo } from './Logo'
import Link from 'next/link'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const { user, authenticated, logout } = useAuth()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      {authenticated && (
        <header className="border-b border-border bg-card/50 backdrop-blur-lg sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/home">
              <Logo size="md" />
            </Link>

            <nav className="flex items-center gap-6">
              <Link href="/home" className="text-sm hover:text-primary transition-colors">
                Feed
              </Link>
              {user && (
                <>
                  <Link
                    href={`/profile/${user.id}`}
                    className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                  >
                    <UserAvatar user={user} size="sm" />
                    <div className="text-sm">
                      <div className="font-medium">{user.display_name || 'User'}</div>
                      <div className="text-xs text-muted-foreground">
                        {user.tokens ? Math.round(user.tokens) : 0} coins
                      </div>
                    </div>
                  </Link>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </>
              )}
            </nav>
          </div>
        </header>
      )}

      {/* Main Content */}
      <main>{children}</main>
    </div>
  )
}
