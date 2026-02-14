# Error Prevention Framework

This document outlines the systematic approach to preventing errors in the Prophecy application.

## 1. Error Boundary System

### Implementation
- **ErrorBoundary Component**: Catches all React rendering errors
- **Location**: `/src/components/ErrorBoundary.tsx`
- **Usage**: Wraps entire app in `providers.tsx`

### Features
- Catches component rendering errors
- Displays user-friendly error messages
- Provides "Refresh" and "Go Home" recovery options
- Logs errors to console for debugging

## 2. Safe Data Access Utilities

### Location
`/src/lib/errorHandler.ts`

### Functions

#### `safeGet<T>(obj, path, defaultValue)`
Prevents "cannot read property of undefined" errors
```typescript
const tokens = safeGet(user, 'tokens', 0)
```

#### `safeNumber(value, decimals)`
Safely formats numbers, returns '0' if invalid
```typescript
const balance = safeNumber(user?.tokens, 2)
```

#### `safeString(value, fallback)`
Safely converts to string with fallback
```typescript
const name = safeString(user?.display_name, 'Anonymous')
```

#### `handleApiError(error)`
Standardizes API error messages
```typescript
try {
  await api.call()
} catch (err) {
  setError(handleApiError(err))
}
```

## 3. Common Error Patterns to Avoid

### ❌ Bad: Direct Object Rendering
```typescript
<div>{user}</div>  // Error: Objects are not valid as React child
```

### ✅ Good: Access Specific Properties
```typescript
<div>{user?.display_name || 'Anonymous'}</div>
```

### ❌ Bad: No Null Check
```typescript
<div>{user.tokens.toFixed(2)}</div>
```

### ✅ Good: Safe Access
```typescript
<div>{user?.tokens ? user.tokens.toFixed(2) : '0'}</div>
```

## 4. Font Standardization

All components use Google Sans:
- Set in `globals.css` as default font family
- Explicitly added to chart components
- Applied via Tailwind config

## 5. Light Mode Consistency

All components updated to use semantic color tokens:
- `bg-card` instead of `bg-dark`
- `text-foreground` instead of `text-white`
- `border-border` instead of `border-white/10`
- `text-muted-foreground` instead of `text-white/60`
