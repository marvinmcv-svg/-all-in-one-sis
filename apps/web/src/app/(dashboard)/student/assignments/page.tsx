'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  FileText,
  Search,
  Clock,
  CheckCircle,
  AlertCircle,
  Upload,
  Calendar,
  BookOpen,
  Filter,
  ChevronRight,
} from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'

// Mock data
const mockAssignments = [
  {
    id: 1,
    title: 'CS 101 Midterm Exam',
    course: 'Introduction to Programming',
    courseCode: 'CS 101',
    dueDate: '2026-03-15',
    dueTime: '9:00 AM',
    status: 'upcoming',
    type: 'exam',
    description: 'Topics covered: Variables, Control Structures, Functions, Basic Data Structures',
    points: 100,
  },
  {
    id: 2,
    title: 'MATH 201 Assignment 5',
    course: 'Calculus II',
    courseCode: 'MATH 201',
    dueDate: '2026-03-18',
    dueTime: '11:59 PM',
    status: 'upcoming',
    type: 'assignment',
    description: 'Integration techniques practice problems',
    points: 50,
  },
  {
    id: 3,
    title: 'ENG 102 Essay',
    course: 'English Composition',
    courseCode: 'ENG 102',
    dueDate: '2026-03-20',
    dueTime: '11:59 PM',
    status: 'upcoming',
    type: 'essay',
    description: 'Write a 5-page argumentative essay on a topic of your choice',
    points: 100,
  },
  {
    id: 4,
    title: 'PHY 101 Lab Report',
    course: 'Physics I',
    courseCode: 'PHY 101',
    dueDate: '2026-03-22',
    dueTime: '5:00 PM',
    status: 'upcoming',
    type: 'lab',
    description: 'Lab report on momentum and energy conservation experiment',
    points: 30,
  },
  {
    id: 5,
    title: 'CS 201 Quiz 4',
    course: 'Data Structures',
    courseCode: 'CS 201',
    dueDate: '2026-03-10',
    dueTime: '2:00 PM',
    status: 'submitted',
    type: 'quiz',
    submittedDate: '2026-03-10',
    points: 25,
    grade: 'A-',
  },
  {
    id: 6,
    title: 'MATH 201 Quiz 3',
    course: 'Calculus II',
    courseCode: 'MATH 201',
    dueDate: '2026-03-05',
    dueTime: '11:59 PM',
    status: 'graded',
    type: 'quiz',
    submittedDate: '2026-03-05',
    grade: 'B+',
    points: 22,
    maxPoints: 25,
  },
  {
    id: 7,
    title: 'CS 101 Lab 4',
    course: 'Introduction to Programming',
    courseCode: 'CS 101',
    dueDate: '2026-03-01',
    dueTime: '11:59 PM',
    status: 'graded',
    type: 'lab',
    submittedDate: '2026-03-01',
    grade: 'A',
    points: 48,
    maxPoints: 50,
  },
  {
    id: 8,
    title: 'ENG 102 Writing Sample',
    course: 'English Composition',
    courseCode: 'ENG 102',
    dueDate: '2026-02-25',
    dueTime: '11:59 PM',
    status: 'graded',
    type: 'essay',
    submittedDate: '2026-02-25',
    grade: 'A+',
    points: 95,
    maxPoints: 100,
  },
]

const upcomingAssignments = mockAssignments.filter((a) => a.status === 'upcoming')
const submittedAssignments = mockAssignments.filter((a) => a.status === 'submitted')
const gradedAssignments = mockAssignments.filter((a) => a.status === 'graded')

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'upcoming':
      return <Clock className="h-4 w-4 text-blue-500" />
    case 'submitted':
      return <CheckCircle className="h-4 w-4 text-yellow-500" />
    case 'graded':
      return <CheckCircle className="h-4 w-4 text-green-500" />
    default:
      return null
  }
}

const getTypeBadge = (type: string) => {
  const colors: Record<string, string> = {
    exam: 'bg-red-100 text-red-800',
    assignment: 'bg-blue-100 text-blue-800',
    essay: 'bg-purple-100 text-purple-800',
    lab: 'bg-green-100 text-green-800',
    quiz: 'bg-yellow-100 text-yellow-800',
  }
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colors[type] || ''}`}>
      {type.charAt(0).toUpperCase() + type.slice(1)}
    </span>
  )
}

const getDaysUntilDue = (dueDate: string) => {
  const today = new Date()
  const due = new Date(dueDate)
  const diff = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return 'Overdue'
  if (diff === 0) return 'Due today'
  if (diff === 1) return 'Due tomorrow'
  return `${diff} days left`
}

export default function AssignmentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAssignment, setSelectedAssignment] = useState<(typeof mockAssignments)[0] | null>(null)

  const filteredAssignments = mockAssignments.filter(
    (assignment) =>
      assignment.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      assignment.course.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assignments</h1>
          <p className="text-muted-foreground">
            View and manage your assignments
          </p>
        </div>
        <Button>
          <Upload className="mr-2 h-4 w-4" />
          Upload Assignment
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockAssignments.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
            <AlertCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{upcomingAssignments.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{submittedAssignments.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Graded</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{gradedAssignments.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="submitted">Submitted</TabsTrigger>
          <TabsTrigger value="graded">Graded</TabsTrigger>
        </TabsList>

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search assignments..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select defaultValue="all-courses">
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by course" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all-courses">All Courses</SelectItem>
                  <SelectItem value="cs101">CS 101</SelectItem>
                  <SelectItem value="math201">MATH 201</SelectItem>
                  <SelectItem value="eng102">ENG 102</SelectItem>
                  <SelectItem value="phy101">PHY 101</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* All Assignments */}
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Assignments</CardTitle>
              <CardDescription>Complete list of all assignments</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {filteredAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="p-4 hover:bg-muted/50 cursor-pointer flex items-center gap-4"
                    onClick={() => setSelectedAssignment(assignment)}
                  >
                    <div className="flex-shrink-0">
                      {getStatusIcon(assignment.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{assignment.title}</p>
                        {getTypeBadge(assignment.type)}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        <span>{assignment.course}</span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3 text-muted-foreground" />
                        <span>{assignment.dueDate}</span>
                      </div>
                      {assignment.status === 'upcoming' && (
                        <p className={`text-xs ${getDaysUntilDue(assignment.dueDate) === 'Overdue' ? 'text-red-600' : 'text-muted-foreground'}`}>
                          {getDaysUntilDue(assignment.dueDate)}
                        </p>
                      )}
                      {assignment.status === 'graded' && (
                        <p className="text-xs font-medium text-green-600">
                          Grade: {assignment.grade}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Upcoming */}
        <TabsContent value="upcoming" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Assignments</CardTitle>
              <CardDescription>Assignments due soon</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {upcomingAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="p-4 hover:bg-muted/50 cursor-pointer flex items-center gap-4"
                    onClick={() => setSelectedAssignment(assignment)}
                  >
                    <div className="flex-shrink-0 p-2 bg-blue-100 rounded-lg">
                      <Clock className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium truncate">{assignment.title}</p>
                        {getTypeBadge(assignment.type)}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        <span>{assignment.course}</span>
                        <span>•</span>
                        <span>{assignment.points} points</span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="flex items-center gap-1 text-sm">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span>{assignment.dueTime}</span>
                      </div>
                      <p className={`text-xs ${getDaysUntilDue(assignment.dueDate) === 'Overdue' ? 'text-red-600' : 'text-blue-600'} font-medium`}>
                        {getDaysUntilDue(assignment.dueDate)}
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Submitted */}
        <TabsContent value="submitted" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Submitted</CardTitle>
              <CardDescription>Awaiting grading</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {submittedAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="p-4 hover:bg-muted/50 cursor-pointer flex items-center gap-4"
                    onClick={() => setSelectedAssignment(assignment)}
                  >
                    <div className="flex-shrink-0 p-2 bg-yellow-100 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{assignment.title}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        <span>{assignment.course}</span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-xs text-muted-foreground">
                        Submitted {assignment.submittedDate}
                      </p>
                      <p className="text-xs text-yellow-600">Awaiting grade</p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Graded */}
        <TabsContent value="graded" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Graded</CardTitle>
              <CardDescription>Completed and graded assignments</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {gradedAssignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="p-4 hover:bg-muted/50 cursor-pointer flex items-center gap-4"
                    onClick={() => setSelectedAssignment(assignment)}
                  >
                    <div className="flex-shrink-0 p-2 bg-green-100 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{assignment.title}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        <span>{assignment.course}</span>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-lg font-bold text-green-600">{assignment.grade}</p>
                      <p className="text-xs text-muted-foreground">
                        {assignment.points}/{assignment.maxPoints} pts
                      </p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Assignment Detail Modal */}
      {selectedAssignment && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setSelectedAssignment(null)}
        >
          <div
            className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <Card className="border-0 shadow-none">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-muted-foreground">{selectedAssignment.courseCode}</span>
                      {getTypeBadge(selectedAssignment.type)}
                    </div>
                    <CardTitle className="text-2xl">{selectedAssignment.title}</CardTitle>
                  </div>
                  {selectedAssignment.status === 'graded' && (
                    <div className="text-right">
                      <p className="text-3xl font-bold text-green-600">{selectedAssignment.grade}</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedAssignment.points}/{selectedAssignment.maxPoints} points
                      </p>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Status */}
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                  selectedAssignment.status === 'upcoming' ? 'bg-blue-100 text-blue-800' :
                  selectedAssignment.status === 'submitted' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {getStatusIcon(selectedAssignment.status)}
                  {selectedAssignment.status.charAt(0).toUpperCase() + selectedAssignment.status.slice(1)}
                </div>

                {/* Description */}
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-sm text-muted-foreground">{selectedAssignment.description}</p>
                </div>

                {/* Info Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Course</p>
                    <p className="font-medium">{selectedAssignment.course}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Points</p>
                    <p className="font-medium">{selectedAssignment.points} points</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-xs text-muted-foreground">Due Date</p>
                    <p className="font-medium">{selectedAssignment.dueDate} at {selectedAssignment.dueTime}</p>
                  </div>
                  {selectedAssignment.submittedDate && (
                    <div className="p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">Submitted</p>
                      <p className="font-medium">{selectedAssignment.submittedDate}</p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t">
                  {selectedAssignment.status === 'upcoming' && (
                    <>
                      <Button className="flex-1">
                        <Upload className="mr-2 h-4 w-4" />
                        Submit Assignment
                      </Button>
                      <Button variant="outline">
                        <FileText className="mr-2 h-4 w-4" />
                        View Details
                      </Button>
                    </>
                  )}
                  {selectedAssignment.status === 'submitted' && (
                    <Button variant="outline" className="flex-1">
                      <FileText className="mr-2 h-4 w-4" />
                      View Submission
                    </Button>
                  )}
                  {selectedAssignment.status === 'graded' && (
                    <>
                      <Button className="flex-1">
                        <FileText className="mr-2 h-4 w-4" />
                        View Feedback
                      </Button>
                      <Button variant="outline">
                        <FileText className="mr-2 h-4 w-4" />
                        View Submission
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
