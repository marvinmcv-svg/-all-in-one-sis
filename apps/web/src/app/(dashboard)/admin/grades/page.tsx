'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  FileText,
  Download,
  Search,
  Plus,
  Edit,
  Eye,
  BarChart3,
  Calendar,
  GraduationCap,
  CheckCircle,
  Clock,
  AlertCircle,
} from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'

// Mock data
const mockExams = [
  {
    id: 1,
    name: 'Midterm Exam - CS 101',
    course: 'Introduction to Programming',
    date: '2026-03-15',
    totalStudents: 45,
    graded: 42,
    status: 'in-progress',
  },
  {
    id: 2,
    name: 'Quiz 3 - MATH 201',
    course: 'Calculus II',
    date: '2026-03-10',
    totalStudents: 38,
    graded: 38,
    status: 'completed',
  },
  {
    id: 3,
 name: 'Final Exam - ENG 102',
    course: 'English Composition',
    date: '2026-03-20',
    totalStudents: 32,
    graded: 0,
    status: 'upcoming',
  },
  {
    id: 4,
    name: 'Lab Exam - PHY 101',
    course: 'Physics I',
    date: '2026-03-12',
    totalStudents: 28,
    graded: 25,
    status: 'in-progress',
  },
]

const mockGradeEntries = [
  { id: 1, studentId: 'STU001', studentName: 'Sarah Johnson', exam: 'CS 101 Midterm', score: 92, grade: 'A' },
  { id: 2, studentId: 'STU002', studentName: 'Michael Chen', exam: 'CS 101 Midterm', score: 88, grade: 'B+' },
  { id: 3, studentId: 'STU003', studentName: 'Emily Davis', exam: 'CS 101 Midterm', score: 95, grade: 'A' },
  { id: 4, studentId: 'STU004', studentName: 'James Wilson', exam: 'CS 101 Midterm', score: 78, grade: 'C+' },
  { id: 5, studentId: 'STU005', studentName: 'Sophia Martinez', exam: 'CS 101 Midterm', score: 85, grade: 'B' },
]

export default function GradesPage() {
  const [selectedExam, setSelectedExam] = useState<(typeof mockExams)[0] | null>(null)
  const [isGradeEntryOpen, setIsGradeEntryOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const handleViewExam = (exam: (typeof mockExams)[0]) => {
    setSelectedExam(exam)
    setIsGradeEntryOpen(true)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Completed
          </span>
        )
      case 'in-progress':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="mr-1 h-3 w-3" />
            In Progress
          </span>
        )
      case 'upcoming':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <AlertCircle className="mr-1 h-3 w-3" />
            Upcoming
          </span>
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Grade Management</h1>
          <p className="text-muted-foreground">
            Manage exams, enter grades, and generate reports
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Exam
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Exams</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{mockExams.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockExams.filter((e) => e.status === 'completed').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {mockExams.filter((e) => e.status === 'in-progress').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Grade</CardTitle>
            <BarChart3 className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">B+</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="exams" className="space-y-4">
        <TabsList>
          <TabsTrigger value="exams">Exams</TabsTrigger>
          <TabsTrigger value="grade-entry">Grade Entry</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="exams" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Exams</CardTitle>
              <CardDescription>Manage exams and view grading progress</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Exam Name</TableHead>
                    <TableHead>Course</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Progress</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockExams.map((exam) => (
                    <TableRow key={exam.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{exam.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>{exam.course}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          {exam.date}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[100px]">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{ width: `${(exam.graded / exam.totalStudents) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {exam.graded}/{exam.totalStudents}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(exam.status)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => handleViewExam(exam)}>
                            <Eye className="mr-1 h-4 w-4" />
                            View
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="mr-1 h-4 w-4" />
                            Edit
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="grade-entry" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Grade Entry</CardTitle>
              <CardDescription>Enter and manage student grades</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <Select defaultValue="cs101">
                  <SelectTrigger className="w-[250px]">
                    <SelectValue placeholder="Select Course" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cs101">CS 101 - Introduction to Programming</SelectItem>
                    <SelectItem value="math201">MATH 201 - Calculus II</SelectItem>
                    <SelectItem value="eng102">ENG 102 - English Composition</SelectItem>
                  </SelectContent>
                </Select>
                <Select defaultValue="midterm">
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select Exam" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="midterm">Midterm Exam</SelectItem>
                    <SelectItem value="quiz3">Quiz 3</SelectItem>
                    <SelectItem value="final">Final Exam</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student ID</TableHead>
                    <TableHead>Student Name</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockGradeEntries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-mono">{entry.studentId}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <GraduationCap className="h-4 w-4 text-muted-foreground" />
                          {entry.studentName}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Input type="number" defaultValue={entry.score} className="w-20" />
                      </TableCell>
                      <TableCell>
                        <Select defaultValue={entry.grade}>
                          <SelectTrigger className="w-20">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="A">A</SelectItem>
                            <SelectItem value="A-">A-</SelectItem>
                            <SelectItem value="B+">B+</SelectItem>
                            <SelectItem value="B">B</SelectItem>
                            <SelectItem value="B-">B-</SelectItem>
                            <SelectItem value="C+">C+</SelectItem>
                            <SelectItem value="C">C</SelectItem>
                            <SelectItem value="F">F</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm">Save</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generate Reports</CardTitle>
              <CardDescription>Create and download grade reports</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
                  <FileText className="h-8 w-8 text-primary mb-2" />
                  <h3 className="font-medium">Student Report Card</h3>
                  <p className="text-sm text-muted-foreground">
                    Generate individual student report cards
                  </p>
                </div>
                <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
                  <BarChart3 className="h-8 w-8 text-primary mb-2" />
                  <h3 className="font-medium">Class Performance</h3>
                  <p className="text-sm text-muted-foreground">
                    View overall class performance metrics
                  </p>
                </div>
                <div className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer">
                  <Download className="h-8 w-8 text-primary mb-2" />
                  <h3 className="font-medium">Bulk Export</h3>
                  <p className="text-sm text-muted-foreground">
                    Export all grades to CSV/Excel
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Grade Entry Dialog */}
      <Dialog open={isGradeEntryOpen} onOpenChange={setIsGradeEntryOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Grade Entry</DialogTitle>
            <DialogDescription>
              Enter grades for {selectedExam?.name}
            </DialogDescription>
          </DialogHeader>
          {selectedExam && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Course</p>
                  <p className="font-medium">{selectedExam.course}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Date</p>
                  <p className="font-medium">{selectedExam.date}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Progress</p>
                  <p className="font-medium">
                    {selectedExam.graded}/{selectedExam.totalStudents} graded
                  </p>
                </div>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Grade</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockGradeEntries.slice(0, 5).map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>{entry.studentName}</TableCell>
                      <TableCell>
                        <Input type="number" defaultValue={entry.score} className="w-20" />
                      </TableCell>
                      <TableCell>
                        <Select defaultValue={entry.grade}>
                          <SelectTrigger className="w-20">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="A">A</SelectItem>
                            <SelectItem value="B+">B+</SelectItem>
                            <SelectItem value="B">B</SelectItem>
                            <SelectItem value="C+">C+</SelectItem>
                            <SelectItem value="C">C</SelectItem>
                            <SelectItem value="F">F</SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsGradeEntryOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setIsGradeEntryOpen(false)}>Save All Grades</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
