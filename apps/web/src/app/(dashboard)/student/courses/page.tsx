'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  BookOpen,
  Search,
  Clock,
  Users,
  GraduationCap,
  FileText,
  Play,
  CheckCircle,
  ChevronRight,
} from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// Mock data
const mockCourses = [
  {
    id: 1,
    name: 'Introduction to Programming',
    code: 'CS 101',
    teacher: 'Prof. Michael Chen',
    schedule: 'Mon/Wed 9:00 AM - 10:30 AM',
    room: 'Room 101',
    credits: 4,
    progress: 75,
    grade: 'A',
    students: 45,
    description: 'Learn the fundamentals of programming using Python. Topics include variables, control structures, functions, and basic data structures.',
    nextClass: 'Tomorrow 9:00 AM',
  },
  {
    id: 2,
    name: 'Calculus II',
    code: 'MATH 201',
    teacher: 'Prof. Emily Davis',
    schedule: 'Tue/Thu 11:00 AM - 12:30 PM',
    room: 'Room 203',
    credits: 4,
    progress: 60,
    grade: 'A-',
    students: 38,
    description: 'Continuation of Calculus I. Topics include integration techniques, sequences, series, and improper integrals.',
    nextClass: 'Today 11:00 AM',
  },
  {
    id: 3,
    name: 'English Composition',
    code: 'ENG 102',
    teacher: 'Prof. Sarah Miller',
    schedule: 'Fri 2:00 PM - 4:00 PM',
    room: 'Room 105',
    credits: 3,
    progress: 90,
    grade: 'A+',
    students: 32,
    description: 'Develop advanced writing skills for academic and professional contexts. Focus on argumentation, research, and revision.',
    nextClass: 'Friday 2:00 PM',
  },
  {
    id: 4,
    name: 'Physics I',
    code: 'PHY 101',
    teacher: 'Prof. James Wilson',
    schedule: 'Mon/Wed/Fri 10:00 AM - 11:00 AM',
    room: 'Lab 301',
    credits: 4,
    progress: 45,
    grade: 'B+',
    students: 28,
    description: 'Introduction to classical mechanics. Topics include kinematics, Newton\'s laws, energy, and momentum.',
    nextClass: 'Today 10:00 AM',
  },
  {
    id: 5,
    name: 'Data Structures',
    code: 'CS 201',
    teacher: 'Prof. Michael Chen',
    schedule: 'Tue/Thu 2:00 PM - 3:30 PM',
    room: 'Room 101',
    credits: 4,
    progress: 30,
    grade: 'B',
    students: 35,
    description: 'Advanced programming concepts including arrays, linked lists, trees, graphs, and algorithm analysis.',
    nextClass: 'Today 2:00 PM',
  },
]

const recentMaterials = [
  { id: 1, title: 'Lecture 10: Recursion', course: 'CS 101', date: '2 days ago' },
  { id: 2, title: 'Chapter 5: Integration Techniques', course: 'MATH 201', date: '3 days ago' },
  { id: 3, title: 'Writing Workshop Slides', course: 'ENG 102', date: '1 week ago' },
]

export default function CoursesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<(typeof mockCourses)[0] | null>(null)

  const filteredCourses = mockCourses.filter(
    (course) =>
      course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.code.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalCredits = mockCourses.reduce((sum, course) => sum + course.credits, 0)
  const averageGrade = mockCourses.reduce((sum, course) => {
    const gradeMap: Record<string, number> = { 'A+': 4.0, A: 4.0, 'A-': 3.7, 'B+': 3.3, B: 3.0, 'B-': 2.7, 'C+': 2.3, C: 2.0 }
    return sum + (gradeMap[course.grade] || 0)
  }, 0) / mockCourses.length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">My Courses</h1>
          <p className="text-muted-foreground">
            View and manage your enrolled courses
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <FileText className="mr-2 h-4 w-4" />
            Course Materials
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enrolled Courses</CardTitle>
            <BookOpen className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockCourses.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Credits</CardTitle>
            <GraduationCap className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalCredits}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Grade</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{averageGrade.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Week</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">15</div>
            <p className="text-xs text-muted-foreground">Class hours</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select defaultValue="all">
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Courses</SelectItem>
                <SelectItem value="active">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Course Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredCourses.map((course) => (
          <Card
            key={course.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => setSelectedCourse(course)}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{course.code}</p>
                  <CardTitle className="text-lg mt-1">{course.name}</CardTitle>
                </div>
                <span className="text-lg font-bold text-primary">{course.grade}</span>
              </div>
              <CardDescription className="mt-2">{course.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Progress */}
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">{course.progress}%</span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${course.progress}%` }}
                  />
                </div>
              </div>

              {/* Details */}
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>{course.teacher}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  <span>{course.schedule}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <GraduationCap className="h-4 w-4" />
                  <span>{course.credits} credits</span>
                </div>
              </div>

              {/* Next Class */}
              <div className="pt-2 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Next class</span>
                  <span className="text-sm font-medium">{course.nextClass}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Course Detail Modal */}
      {selectedCourse && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setSelectedCourse(null)}
        >
          <div
            className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <Card className="border-0 shadow-none">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{selectedCourse.code}</p>
                    <CardTitle className="text-2xl">{selectedCourse.name}</CardTitle>
                  </div>
                  <span className="text-2xl font-bold text-primary">{selectedCourse.grade}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Description */}
                <div>
                  <h3 className="font-semibold mb-2">About this course</h3>
                  <p className="text-sm text-muted-foreground">{selectedCourse.description}</p>
                </div>

                {/* Progress */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="font-medium">Course Progress</span>
                    <span className="font-medium">{selectedCourse.progress}%</span>
                  </div>
                  <div className="h-3 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${selectedCourse.progress}%` }}
                    />
                  </div>
                </div>

                {/* Info Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Instructor</p>
                    <p className="font-medium">{selectedCourse.teacher}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Schedule</p>
                    <p className="font-medium">{selectedCourse.schedule}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Room</p>
                    <p className="font-medium">{selectedCourse.room}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Credits</p>
                    <p className="font-medium">{selectedCourse.credits}</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button className="flex-1">
                    <Play className="mr-2 h-4 w-4" />
                    Continue Learning
                  </Button>
                  <Button variant="outline">
                    <FileText className="mr-2 h-4 w-4" />
                    Materials
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
