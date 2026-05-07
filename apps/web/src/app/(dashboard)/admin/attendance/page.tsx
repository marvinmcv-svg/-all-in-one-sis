'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Calendar,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  Filter,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// Mock data
const mockAttendance = [
  { id: 1, studentId: 'STU001', studentName: 'Sarah Johnson', present: true, time: '8:00 AM' },
  { id: 2, studentId: 'STU002', studentName: 'Michael Chen', present: true, time: '8:02 AM' },
  { id: 3, studentId: 'STU003', studentName: 'Emily Davis', present: false, time: '-' },
  { id: 4, studentId: 'STU004', studentName: 'James Wilson', present: true, time: '7:58 AM' },
  { id: 5, studentId: 'STU005', studentName: 'Sophia Martinez', present: true, time: '8:01 AM' },
  { id: 6, studentId: 'STU006', studentName: 'David Brown', present: false, time: '-' },
  { id: 7, studentId: 'STU007', studentName: 'Olivia Taylor', present: true, time: '8:00 AM' },
  { id: 8, studentId: 'STU008', studentName: 'William Anderson', present: true, time: '7:55 AM' },
]

interface AttendanceRecord {
  id: number
  studentId: string
  studentName: string
  present: boolean
  time: string
}

export default function AttendancePage() {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date())
  const [selectedClass, setSelectedClass] = useState<string>('')
  const [attendanceData, setAttendanceData] = useState<AttendanceRecord[]>(mockAttendance)

  const handlePrevDay = () => {
    const prev = new Date(selectedDate)
    prev.setDate(prev.getDate() - 1)
    setSelectedDate(prev)
  }

  const handleNextDay = () => {
    const next = new Date(selectedDate)
    next.setDate(next.getDate() + 1)
    setSelectedDate(next)
  }

  const toggleAttendance = (id: number) => {
    setAttendanceData((prev) =>
      prev.map((record) =>
        record.id === id
          ? {
              ...record,
              present: !record.present,
              time: !record.present ? new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '-',
            }
          : record
      )
    )
  }

  const markAllPresent = () => {
    setAttendanceData((prev) =>
      prev.map((record) => ({
        ...record,
        present: true,
        time: new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      }))
    )
  }

  const markAllAbsent = () => {
    setAttendanceData((prev) =>
      prev.map((record) => ({
        ...record,
        present: false,
        time: '-',
      }))
    )
  }

  const presentCount = attendanceData.filter((r) => r.present).length
  const absentCount = attendanceData.filter((r) => !r.present).length
  const attendanceRate = Math.round((presentCount / attendanceData.length) * 100)

  const formattedDate = selectedDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Attendance Management</h1>
          <p className="text-muted-foreground">
            Track and manage student attendance
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Date Selector */}
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" onClick={handlePrevDay}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <div className="flex items-center gap-2 px-4 py-2 border rounded-md min-w-[250px]">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{formattedDate}</span>
              </div>
              <Button variant="outline" size="icon" onClick={handleNextDay}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Class Selector */}
            <Select value={selectedClass} onValueChange={setSelectedClass}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select Class" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="cs101">CS 101 - Grade 10A</SelectItem>
                <SelectItem value="math201">MATH 201 - Grade 11A</SelectItem>
                <SelectItem value="eng102">ENG 102 - Grade 9B</SelectItem>
                <SelectItem value="phy101">PHY 101 - Grade 12A</SelectItem>
              </SelectContent>
            </Select>

            {/* Quick Actions */}
            <div className="flex gap-2 lg:ml-auto">
              <Button variant="outline" size="sm" onClick={markAllPresent}>
                <CheckCircle className="mr-2 h-4 w-4" />
                Mark All Present
              </Button>
              <Button variant="outline" size="sm" onClick={markAllAbsent}>
                <XCircle className="mr-2 h-4 w-4" />
                Mark All Absent
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{attendanceData.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Present</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{presentCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Absent</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{absentCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
            <AlertCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{attendanceRate}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Attendance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Attendance List</CardTitle>
          <CardDescription>
            Click on a student to toggle their attendance status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student ID</TableHead>
                <TableHead>Student Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Check-in Time</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {attendanceData.map((record) => (
                <TableRow key={record.id}>
                  <TableCell className="font-mono text-sm">{record.studentId}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${record.present ? 'bg-green-500' : 'bg-red-500'}`} />
                      <span className="font-medium">{record.studentName}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        record.present
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {record.present ? 'Present' : 'Absent'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      {record.time}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant={record.present ? 'destructive' : 'default'}
                      size="sm"
                      onClick={() => toggleAttendance(record.id)}
                    >
                      {record.present ? 'Mark Absent' : 'Mark Present'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
