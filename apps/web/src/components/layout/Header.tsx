'use client'

import { useSession, signOut } from 'next-auth/react'
import { Bell, User, LogOut, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface HeaderProps {
  onMenuClick?: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { data: session } = useSession()

  const roleLabel = session?.user?.role?.toUpperCase() || 'USER'
  const userEmail = session?.user?.email || 'user@example.com'

  return (
    <div className="h-16 flex-shrink-0 flex bg-white shadow">
      <div className="flex-1 flex px-4 justify-between items-center">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onMenuClick}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="hidden sm:block ml-4 text-sm text-muted-foreground">
            {roleLabel} Portal
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <Button variant="ghost" size="icon" className="relative">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
          </Button>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
              <User className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="hidden sm:block text-sm font-medium">{userEmail}</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => signOut({ callbackUrl: '/login' })}
            className="text-gray-400 hover:text-red-500"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
