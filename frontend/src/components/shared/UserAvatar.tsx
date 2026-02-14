'use client'

import Image from 'next/image'

interface UserAvatarProps {
  user: {
    display_name: string
    avatar_url?: string | null
  }
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const sizeMap = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
  xl: 'w-16 h-16 text-lg',
}

export function UserAvatar({ user, size = 'md', className = '' }: UserAvatarProps) {
  const sizeClass = sizeMap[size]
  const initials = user.display_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  if (user.avatar_url) {
    return (
      <div className={`relative rounded-full overflow-hidden ${sizeClass} ${className}`}>
        <Image
          src={user.avatar_url}
          alt={user.display_name}
          fill
          className="object-cover"
        />
      </div>
    )
  }

  return (
    <div
      className={`${sizeClass} ${className} rounded-full bg-[#19747E] flex items-center justify-center font-bold text-white`}
    >
      {initials}
    </div>
  )
}
