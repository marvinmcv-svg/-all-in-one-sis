'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  UserPlus,
  Search,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  Users,
  Mail,
  Phone,
  BookOpen,
  Filter,
} from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
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

// Mock data
const mockTeachers = [
  {
    id: 1,
    firstName: 'Michael',
    lastName: 'Chen',
    email: 'michael.chen@school.edu',
    phone: '+1 234-567-8901',
    department: 'Computer Science',
    courses: 4,
    hireDate: '2020-08-15',
    status: 'active',
  },
  {
    id: 2,
    firstName: 'Emily',
    lastName: 'Davis',
    email: 'emily.davis@school.edu',
    phone: '+1 234-567-8902',
    department: 'Mathematics',
    courses: 3,
    hireDate: '2019-08-20',
    status: 'active',
  },
  {
    id: 3,
    firstName: 'Sarah',
    lastName: 'Miller',
    email: 'sarah.miller@school.edu',
    phone: '+1 234-567-8903',
    department: 'English',
    courses: 5,
    hireDate: '2021-08-10',
    status: 'active',
  },
  {
    id: 4,
    firstName: 'James',
    lastName: 'Wilson',
    email: 'james.wilson@school.edu',
    phone: '+1 234-567-8904',
    department: 'Physics',
    courses: 3,
    hireDate: '2018-08-25',
    status: 'active',
  },
  {
    id: 5,
    firstName: 'Lisa',
    lastName: 'Anderson',
    email: 'lisa.anderson@school.edu',
    phone: '+1 234-567-8905',
    department: 'Chemistry',
    courses: 4,
    hireDate: '2022-08-15',
    status: 'inactive',
  },
]

interface TeacherFormData {
  firstName: string
  lastName: string
  email: string
  phone: string
  department: string
}

export default function TeachersPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState<string>('')
  const [selectedTeacher, setSelectedTeacher] = useState<(typeof mockTeachers)[0] | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [formData, setFormData] = useState<TeacherFormData>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    department: '',
  })

  const filteredTeachers = mockTeachers.filter((teacher) => {
    const matchesSearch =
      teacher.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      teacher.lastName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      teacher.email.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesDepartment = departmentFilter ? teacher.department === departmentFilter : true
    return matchesSearch && matchesDepartment
  })

  const handleViewTeacher = (teacher: (typeof mockTeachers)[0]) => {
    setSelectedTeacher(teacher)
    setIsDetailOpen(true)
  }

  const handleAddTeacher = () => {
    console.log('Adding teacher:', formData)
    setIsAddOpen(false)
    setFormData({
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      department: '',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Teacher Management</h1>
          <p className="text-muted-foreground">
            Manage all teachers in the system
          </p>
        </div>
        <Button onClick={() => setIsAddOpen(true)}>
          <UserPlus className="mr-2 h-4 w-4" />
          Add Teacher
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <select
                className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={departmentFilter}
                onChange={(e) => setDepartmentFilter(e.target.value)}
              >
                <option value="">All Departments</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Mathematics">Mathematics</option>
                <option value="English">English</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
              </select>
              <Button variant="outline">
                <Filter className="mr-2 h-4 w-4" />
                More Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Teachers Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Teachers</CardTitle>
          <CardDescription>
            {filteredTeachers.length} teacher{filteredTeachers.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Courses</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTeachers.map((teacher) => (
                <TableRow key={teacher.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                        <Users className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="font-medium">
                          {teacher.firstName} {teacher.lastName}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Hired: {teacher.hireDate}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-1 text-sm">
                        <Mail className="h-3 w-3" />
                        {teacher.email}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Phone className="h-3 w-3" />
                        {teacher.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{teacher.department}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <BookOpen className="h-4 w-4 text-muted-foreground" />
                      {teacher.courses}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        teacher.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {teacher.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleViewTeacher(teacher)}>
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Teacher Detail Dialog */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Teacher Details</DialogTitle>
            <DialogDescription>
              Detailed information about the teacher
            </DialogDescription>
          </DialogHeader>
          {selectedTeacher && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
                  <Users className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">
                    {selectedTeacher.firstName} {selectedTeacher.lastName}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedTeacher.department}
                  </p>
                </div>
              </div>
              <div className="grid gap-3">
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{selectedTeacher.email}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{selectedTeacher.phone}</span>
                </div>
                <div className="flex items-center gap-3">
                  <BookOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    Teaching {selectedTeacher.courses} courses
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    Hired on {selectedTeacher.hireDate}
                  </span>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDetailOpen(false)}>
              Close
            </Button>
            <Button>Edit Teacher</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Teacher Dialog */}
      <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add New Teacher</DialogTitle>
            <DialogDescription>
              Enter the teacher&apos;s information to add them to the system
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="firstName" className="text-sm font-medium">
                  First Name
                </label>
                <Input
                  id="firstName"
                  value={formData.firstName}
                  onChange={(e) =>
                    setFormData({ ...formData, firstName: e.target.value })
                  }
                  placeholder="John"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="lastName" className="text-sm font-medium">
                  Last Name
                </label>
                <Input
                  id="lastName"
                  value={formData.lastName}
                  onChange={(e) =>
                    setFormData({ ...formData, lastName: e.target.value })
                  }
                  placeholder="Smith"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                placeholder="john.smith@school.edu"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="phone" className="text-sm font-medium">
                Phone
              </label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) =>
                  setFormData({ ...formData, phone: e.target.value })
                }
                placeholder="+1 234-567-8900"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="department" className="text-sm font-medium">
                Department
              </label>
              <select
                id="department"
                className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={formData.department}
                onChange={(e) =>
                  setFormData({ ...formData, department: e.target.value })
                }
              >
                <option value="">Select Department</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Mathematics">Mathematics</option>
                <option value="English">English</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddTeacher}>Add Teacher</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
