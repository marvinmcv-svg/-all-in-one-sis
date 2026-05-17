'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { clsx } from 'clsx'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { href: '/dashboard/track', label: 'Track', icon: '📊' },
  { href: '/dashboard/ai', label: 'AI Coach', icon: '💬' },
  { href: '/dashboard/cbt', label: 'CBT Program', icon: '🧠' },
  { href: '/dashboard/journal', label: 'Journal', icon: '📓' },
  { href: '/dashboard/community', label: 'Community', icon: '🤝' },
  { href: '/dashboard/badges', label: 'Badges', icon: '🏆' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-100">
        <div className="text-xl font-bold text-green-600">ClearPath</div>
        <div className="text-xs text-gray-500 mt-1">Recovery Platform</div>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
              pathname === item.href
                ? 'bg-green-50 text-green-700'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            )}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
