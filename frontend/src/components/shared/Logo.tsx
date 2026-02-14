'use client'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  showText?: boolean
}

const sizeMap = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
}

const textSizeMap = {
  sm: 'text-lg',
  md: 'text-2xl',
  lg: 'text-3xl',
  xl: 'text-5xl',
}

export function Logo({ size = 'md', className = '', showText = true }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <img
        src="/prophecy-logo.png"
        alt="Prophecy Logo"
        className={sizeMap[size]}
      />
      {showText && (
        <div className={`font-bold text-[#19747E] ${textSizeMap[size]}`}>
          PROPHECY
        </div>
      )}
    </div>
  )
}
