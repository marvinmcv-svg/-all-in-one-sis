'use client'

import { useSession } from 'next-auth/react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  BookOpen,
  FileText,
  GraduationCap,
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  TrendingUp,
} from 'lucide-react'

// Mock data
const currentCourses = [
  {
    id: 1,
    name: 'CS 101 - Introduction to Programming',
    teacher: 'Prof. Michael Chen',
    schedule: 'Mon/Wed 9:00 AM',
    progress: 75,
    grade: 'A',
  },
  {
    id: 2,
    name: 'MATH 201 - Calculus II',
    teacher: 'Prof. Emily Davis',
    schedule: 'Tue/Thu 11:00 AM',
    progress: 60,
    grade: 'A-',
  },
  {
    id: 3,
    name: 'ENG 102 - English Composition',
    teacher: 'Prof. Sarah Miller',
    schedule: 'Fri 2:00 PM',
    progress: 90,
    grade: 'A+',
  },
  {
    id: 4,
    name: 'PHY 101 - Physics I',
    teacher: 'Prof. James Wilson',
    schedule: 'Mon/Wed/Fri 10:00 AM',
    progress: 45,
    grade: 'B+',
  },
]

const upcomingAssignments = [
  {
    id: 1,
    title: 'CS 101 Midterm Exam',
    course: 'Introduction to Programming',
    dueDate: 'Mar 15, 2026',
    type: 'exam',
    status: 'upcoming',
  },
  {
    id: 2,
    title: 'MATH 201 Assignment 5',
    course: 'Calculus II',
    dueDate: 'Mar 18, 2026',
    type: 'assignment',
    status: 'upcoming',
  },
  {
    id: 3,
    title: 'ENG 102 Essay',
    course: 'English Composition',
    dueDate: 'Mar 20, 2026',
    type: 'essay',
    status: 'upcoming',
  },
  {
    id: 4,
    title: 'PHY 101 Lab Report',
    course: 'Physics I',
    dueDate: 'Mar 22, 2026',
    type: 'lab',
    status: 'upcoming',
  },
]

const recentGrades = [
  { id: 1, title: 'CS 101 Lab 4', course: 'Introduction to Programming', grade: '95%', weight: 'A' },
  { id: 2, title: 'MATH 201 Quiz 3', course: 'Calculus II', grade: '88%', weight: 'B+' },
  { id: 3, title: 'ENG 102 Writing Sample', course: 'English Composition', grade: '92%', weight: 'A' },
  { id: 4, title: 'PHY 101 Homework 2', course: 'Physics I', grade: '85%', weight: 'B' },
]

const quickLinks = [
  { name: 'View Schedule', href: '/student/courses', icon: Calendar },
  { name: 'Check Assignments', href: '/student/assignments', icon: FileText },
  { name: 'View Grades', href: '/student/grades', icon: GraduationCap },
  { name: 'Course Materials', href: '/student/materials', icon: BookOpen },
]

export default function StudentDashboardPage() {
  const { data: session } = useSession()
  const studentName = session?.user?.name || 'Student'

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, {studentName}!</h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your courses today.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Calendar className="mr-2 h-4 w-4" />
            Schedule
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
            <CardTitle className="text-sm font-medium">Current GPA</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3.75</div>
            <p className="text-xs text-green-500">Dean's List</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Credits</CardTitle>
            <GraduationCap className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">48</div>
            <p className="text-xs text-muted-foreground">120 required</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">96%</div>
            <p className="text-xs text-green-500">Excellent</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-muted-foreground">This semester</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Current Courses */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Current Courses</CardTitle>
              <CardDescription>Your enrolled courses this semester</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <a href="/student/courses">
                View All <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentCourses.map((course) => (
                <div
                  key={course.id}
                  className="flex items-center justify-between p-4 rounded-lg border"
                >
                  <div className="flex-1">
                    <p className="font-medium">{course.name}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{course.teacher}</span>
                      <span>•</span>
                      <Clock className="h-3 w-3" />
                      <span>{course.schedule}</span>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${course.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {course.progress}%
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <span className="text-lg font-bold text-primary">{course.grade}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Links</CardTitle>
            <CardDescription>Frequently accessed features</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            {quickLinks.map((link) => {
              const Icon = link.icon
              return (
                <Button
                  key={link.name}
                  variant="outline"
                  className="justify-start h-auto py-3"
                  asChild
                >
                  <a href={link.href}>
                    <Icon className="mr-3 h-5 w-5" />
                    {link.name}
                  </a>
                </Button>
              )
            })}
          </CardContent>
        </Card>

        {/* Upcoming Assignments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Upcoming</CardTitle>
              <CardDescription>Assignments and exams</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <a href="/student/assignments">
                View All <ArrowRight className="ml-1 h-4 w-4" />
              </a>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {upcomingAssignments.map((assignment) => (
                <div key={assignment.id} className="flex items-start gap-3">
                  <div
                    className={`mt-1 p-1.5 rounded-lg ${
                      assignment.type === 'exam'
                        ? 'bg-red-100 text-red-600'
                        : assignment.type === 'essay'
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-yellow-100 text-yellow-600'
                    }`}
                  >
                    {assignment.type === 'exam' ? (
                      <AlertCircle className="h-4 w-4" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{assignment.title}</p>
                    <p className="text-xs text-muted-foreground">{assignment.course}</p>
                    <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>Due {assignment.dueDate}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Grades */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Grades</CardTitle>
              <CardDescription>Latest graded submissions</CardDescription>
            </div>
            <Button variant="ghost" size="sm">
              View All <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentGrades.map((grade) => (
                <div key={grade.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{grade.title}</p>
                    <p className="text-xs text-muted-foreground">{grade.course}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-primary">{grade.grade}</p>
                    <p className="text-xs text-muted-foreground">Grade: {grade.weight}</p>
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
