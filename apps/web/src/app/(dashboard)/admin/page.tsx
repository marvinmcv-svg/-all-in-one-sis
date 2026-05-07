'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  GraduationCap,
  Users,
  ClipboardCheck,
  DollarSign,
  Plus,
  UserPlus,
  Calendar,
  FileText,
  TrendingUp,
  TrendingDown,
  Activity,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'

// Mock data for charts
const attendanceData = [
  { month: 'Jan', rate: 92 },
  { month: 'Feb', rate: 94 },
  { month: 'Mar', rate: 91 },
  { month: 'Apr', rate: 95 },
  { month: 'May', rate: 93 },
  { month: 'Jun', rate: 96 },
]

const enrollmentData = [
  { month: 'Jan', students: 1200 },
  { month: 'Feb', students: 1250 },
  { month: 'Mar', students: 1280 },
  { month: 'Apr', students: 1320 },
  { month: 'May', students: 1380 },
  { month: 'Jun', students: 1420 },
]

const recentActivities = [
  { id: 1, action: 'New student enrolled', user: 'Sarah Johnson', time: '2 minutes ago', type: 'student' },
  { id: 2, action: 'Grade submitted', user: 'Prof. Michael Chen', time: '15 minutes ago', type: 'grade' },
  { id: 3, action: 'Attendance marked', user: 'Admin', time: '1 hour ago', type: 'attendance' },
  { id: 4, action: 'New teacher added', user: 'Admin', time: '2 hours ago', type: 'teacher' },
  { id: 5, action: 'Course created', user: 'Prof. Emily Davis', time: '3 hours ago', type: 'course' },
]

const quickActions = [
  { name: 'Add Student', icon: UserPlus, href: '/admin/students', color: 'bg-blue-500' },
  { name: 'Add Teacher', icon: Users, href: '/admin/teachers', color: 'bg-green-500' },
  { name: 'Mark Attendance', icon: ClipboardCheck, href: '/admin/attendance', color: 'bg-purple-500' },
  { name: 'Manage Grades', icon: FileText, href: '/admin/grades', color: 'bg-orange-500' },
]

interface KPICardProps {
  title: string
  value: string
  change: string
  changeType: 'increase' | 'decrease'
  icon: React.ElementType
  color: string
}

function KPICard({ title, value, change, changeType, icon: Icon, color }: KPICardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-4 w-4 text-white" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center gap-1 text-xs">
          {changeType === 'increase' ? (
            <TrendingUp className="h-3 w-3 text-green-500" />
          ) : (
            <TrendingDown className="h-3 w-3 text-red-500" />
          )}
          <span className={changeType === 'increase' ? 'text-green-500' : 'text-red-500'}>
            {change}
          </span>
          <span className="text-muted-foreground">from last month</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default function AdminDashboardPage() {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your Student Information System
          </p>
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-[200px]"
          />
          <Button>
            <FileText className="mr-2 h-4 w-4" />
            Reports
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Students"
          value="1,234"
          change="+10%"
          changeType="increase"
          icon={GraduationCap}
          color="bg-blue-500"
        />
        <KPICard
          title="Total Teachers"
          value="56"
          change="+2"
          changeType="increase"
          icon={Users}
          color="bg-green-500"
        />
        <KPICard
          title="Attendance Rate"
          value="94%"
          change="+2%"
          changeType="increase"
          icon={ClipboardCheck}
          color="bg-purple-500"
        />
        <KPICard
          title="Fee Collection"
          value="$128,450"
          change="+15%"
          changeType="increase"
          icon={DollarSign}
          color="bg-orange-500"
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Attendance Trend</CardTitle>
            <CardDescription>Monthly attendance rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={attendanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" fontSize={12} />
                  <YAxis fontSize={12} domain={[85, 100]} />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="rate"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Student Enrollment</CardTitle>
            <CardDescription>Monthly enrollment growth</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={enrollmentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="students" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions and Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common administrative tasks</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.name}
                  variant="outline"
                  className="justify-start h-auto py-3"
                  asChild
                >
                  <a href={action.href}>
                    <div className={`p-2 rounded-lg mr-3 ${action.color}`}>
                      <Icon className="h-4 w-4 text-white" />
                    </div>
                    {action.name}
                  </a>
                </Button>
              )
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest actions in the system</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="mt-1">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">{activity.action}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{activity.user}</span>
                      <span>•</span>
                      <span>{activity.time}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
