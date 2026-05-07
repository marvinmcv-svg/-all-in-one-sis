'use client'

import { useSession } from 'next-auth/react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  BookOpen,
  Users,
  Clock,
  FileText,
  CheckCircle,
  AlertCircle,
  Calendar,
  ArrowRight,
  Plus,
  Megaphone,
  BarChart3,
} from 'lucide-react'

// Mock data
const todaySchedule = [
  { id: 1, time: '9:00 AM', course: 'CS 101 - Introduction to Programming', room: 'Room 101', students: 45 },
  { id: 2, time: '11:00 AM', course: 'CS 201 - Data Structures', room: 'Room 203', students: 38 },
  { id: 3, time: '2:00 PM', course: 'CS 301 - Algorithms', room: 'Room 105', students: 25 },
]

const pendingGrading = [
  { id: 1, title: 'CS 101 Lab 5', course: 'Introduction to Programming', submissions: 42, dueDate: '2 days ago' },
  { id: 2, title: 'CS 201 Assignment 3', course: 'Data Structures', submissions: 35, dueDate: '3 days ago' },
  { id: 3, title: 'CS 301 Quiz 4', course: 'Algorithms', submissions: 22, dueDate: '1 day ago' },
  { id: 4, title: 'CS 101 Quiz 3', course: 'Introduction to Programming', submissions: 45, dueDate: 'Today' },
]

const myCourses = [
  { id: 1, name: 'CS 101 - Introduction to Programming', students: 45, nextClass: 'Today 9:00 AM' },
  { id: 2, name: 'CS 201 - Data Structures', students: 38, nextClass: 'Today 11:00 AM' },
  { id: 3, name: 'CS 301 - Algorithms', students: 25, nextClass: 'Today 2:00 PM' },
  { id: 4, name: 'CS 401 - Machine Learning', students: 20, nextClass: 'Tomorrow 10:00 AM' },
]

const announcements = [
  {
    id: 1,
    title: 'Midterm Exams Schedule',
    content: 'Midterm exams will be held from March 15-20. Please prepare your exam materials.',
    date: '2 hours ago',
    priority: 'high',
  },
  {
    id: 2,
    title: 'Lab Equipment Maintenance',
    content: 'Computer Lab 3 will be closed for maintenance on Saturday.',
    date: '1 day ago',
    priority: 'medium',
  },
  {
    id: 3,
    title: 'New Course Materials Available',
    content: 'Updated course materials for CS 301 are now available on the portal.',
    date: '2 days ago',
    priority: 'low',
  },
]

const quickActions = [
  { name: 'Take Attendance', href: '/admin/attendance', icon: CheckCircle },
  { name: 'Submit Grades', href: '/admin/grades', icon: BarChart3 },
  { name: 'Create Assignment', href: '/teacher/assignments', icon: Plus },
  { name: 'Post Announcement', href: '/teacher/announcements', icon: Megaphone },
]

export default function TeacherDashboardPage() {
  const { data: session } = useSession()
  const teacherName = session?.user?.name || 'Teacher'

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome, {teacherName}!</h1>
          <p className="text-muted-foreground">
            Manage your courses and student progress.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            My Schedule
          </Button>
          <Button>
            <BookOpen className="mr-2 h-4 w-4" />
            My Courses
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">My Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <p className="text-xs text-muted-foreground">This semester</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">128</div>
            <p className="text-xs text-muted-foreground">Across all courses</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Grades</CardTitle>
            <FileText className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">Awaiting submission</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Office Hours</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6</div>
            <p className="text-xs text-muted-foreground">This week</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Today's Schedule */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Today&apos;s Schedule</CardTitle>
              <CardDescription>Your classes for today</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Calendar className="mr-2 h-4 w-4" />
              Full Schedule
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {todaySchedule.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center gap-4 p-4 rounded-lg border"
                >
                  <div className="flex flex-col items-center justify-center w-20">
                    <span className="text-lg font-bold text-primary">{item.time}</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{item.course}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{item.room}</span>
                      <span>•</span>
                      <Users className="h-3 w-3" />
                      <span>{item.students} students</span>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <CheckCircle className="mr-1 h-4 w-4" />
                    Take Attendance
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
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
                    <Icon className="mr-3 h-5 w-5" />
                    {action.name}
                  </a>
                </Button>
              )
            })}
          </CardContent>
        </Card>

        {/* Pending Grade Submissions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Pending Grading</CardTitle>
              <CardDescription>Submissions awaiting review</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <a href="/admin/grades">
                View All <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pendingGrading.map((item) => (
                <div key={item.id} className="flex items-center justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <AlertCircle className="h-4 w-4 text-orange-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-xs text-muted-foreground">{item.course}</p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                        <span>{item.submissions} submissions</span>
                        <span>•</span>
                        <span>Due {item.dueDate}</span>
                      </div>
                    </div>
                  </div>
                  <Button size="sm">Grade</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* My Courses */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>My Courses</CardTitle>
              <CardDescription>Courses you are teaching</CardDescription>
            </div>
            <Button variant="ghost" size="sm">
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {myCourses.map((course) => (
                <div key={course.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{course.name}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Users className="h-3 w-3" />
                      <span>{course.students} students</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Next class</p>
                    <p className="text-xs font-medium">{course.nextClass}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Announcements */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Announcements</CardTitle>
              <CardDescription>Latest announcements</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Megaphone className="mr-2 h-4 w-4" />
              New Announcement
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {announcements.map((announcement) => (
                <div
                  key={announcement.id}
                  className="flex items-start gap-3 p-4 rounded-lg border"
                >
                  <div
                    className={`mt-1 p-2 rounded-lg ${
                      announcement.priority === 'high'
                        ? 'bg-red-100 text-red-600'
                        : announcement.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-600'
                        : 'bg-blue-100 text-blue-600'
                    }`}
                  >
                    <Megaphone className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{announcement.title}</p>
                      <span className="text-xs text-muted-foreground">
                        {announcement.date}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {announcement.content}
                    </p>
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
