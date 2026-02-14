import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'

// Helper function to extract error message from various error formats
function getErrorMessage(error: any): string {
  if (!error) return 'An error occurred'

  // Check for response data
  if (error.response?.data) {
    const data = error.response.data

    // Check for detail string
    if (typeof data.detail === 'string') {
      return data.detail
    }

    // Check for Pydantic validation errors (array format)
    if (Array.isArray(data.detail)) {
      return data.detail.map((err: any) => err.msg || String(err)).join(', ')
    }

    // Check for validation errors in root
    if (Array.isArray(data)) {
      return data.map((err: any) => err.msg || String(err)).join(', ')
    }

    // Check for message field
    if (typeof data.message === 'string') {
      return data.message
    }
  }

  // Fallback to error message
  if (error.message && typeof error.message === 'string') {
    return error.message
  }

  return 'An unexpected error occurred'
}

export function useAuth() {
  const { user, setUser, clearUser } = useAuthStore()
  const [isLoading, setIsLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      try {
        const { data } = await api.get('/users/me')
        setUser(data)
        setAuthenticated(true)
      } catch (error) {
        localStorage.removeItem('auth_token')
        clearUser()
        setAuthenticated(false)
      }
    }
    setIsLoading(false)
  }

  const login = async (email: string, password: string) => {
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('auth_token', data.access_token)
      setUser(data.user)
      setAuthenticated(true)
      return data
    } catch (error: any) {
      const errorMsg = getErrorMessage(error)
      throw new Error(errorMsg)
    }
  }

  const signup = async (email: string, password: string, display_name: string) => {
    try {
      const { data } = await api.post('/auth/signup', { email, password, display_name })
      localStorage.setItem('auth_token', data.access_token)
      setUser(data.user)
      setAuthenticated(true)
      return data
    } catch (error: any) {
      const errorMsg = getErrorMessage(error)
      throw new Error(errorMsg)
    }
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('auth_token')
      clearUser()
      setAuthenticated(false)
    }
  }

  return {
    user,
    authenticated,
    isLoading,
    login,
    signup,
    logout,
  }
}
