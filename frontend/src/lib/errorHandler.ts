/**
 * Central error handling utilities
 * Provides consistent error handling across the application
 */

export class AppError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message)
    this.name = 'AppError'
  }
}

/**
 * Safe value accessor that prevents "cannot read property of undefined" errors
 */
export function safeGet<T>(obj: any, path: string, defaultValue: T): T {
  try {
    const value = path.split('.').reduce((current, key) => current?.[key], obj)
    return value !== undefined && value !== null ? value : defaultValue
  } catch {
    return defaultValue
  }
}

/**
 * Safe number formatter
 */
export function safeNumber(value: any, decimals: number = 0): string {
  const num = Number(value)
  if (isNaN(num)) return '0'
  return num.toFixed(decimals)
}

/**
 * Safe string formatter
 */
export function safeString(value: any, fallback: string = ''): string {
  if (value === null || value === undefined) return fallback
  return String(value)
}

/**
 * API error handler
 */
export function handleApiError(error: any): string {
  if (error.response) {
    // Server responded with error
    return error.response.data?.detail || error.response.data?.message || 'Server error occurred'
  } else if (error.request) {
    // Request made but no response
    return 'No response from server. Please check your connection.'
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred'
  }
}

/**
 * Retry wrapper for async functions
 */
export async function retryAsync<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: any

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }

  throw lastError
}

/**
 * Type guard for checking if object has required properties
 */
export function hasRequiredFields<T>(
  obj: any,
  fields: (keyof T)[]
): obj is T {
  return fields.every(field => obj && obj[field] !== undefined)
}
