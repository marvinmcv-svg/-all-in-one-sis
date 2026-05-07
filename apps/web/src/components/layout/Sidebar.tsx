'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Calendar,
  BarChart3,
  BookOpen,
  FileText,
  ClipboardList,
} from 'lucide-react'

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  roles: string[]
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, roles: ['admin'] },
  { name: 'Students', href: '/admin/students', icon: GraduationCap, roles: ['admin'] },
  { name: 'Teachers', href: '/admin/teachers', icon: Users, roles: ['admin'] },
  { name: 'Attendance', href: '/admin/attendance', icon: ClipboardList, roles: ['admin', 'teacher'] },
  { name: 'Grades', href: '/admin/grades', icon: BarChart3, roles: ['admin', 'teacher'] },
  { name: 'Courses', href: '/student/courses', icon: BookOpen, roles: ['student', 'teacher'] },
  { name: 'Assignments', href: '/student/assignments', icon: FileText, roles: ['student', 'teacher'] },
]

interface SidebarProps {
  userRole?: string
}

export function Sidebar({ userRole = 'admin' }: SidebarProps) {
  const pathname = usePathname()

  const filteredNav = navigation.filter((item) =>
    item.roles.includes(userRole)
  )

  return (
    <div className="flex flex-col w-64 bg-gray-900">
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center h-16 flex-shrink-0 px-4 bg-gray-800">
          <Link href="/admin">
            <h1 className="text-white text-xl font-bold">All-in-One SIS</h1>
          </Link>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {filteredNav.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white',
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors'
                )}
              >
                <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
