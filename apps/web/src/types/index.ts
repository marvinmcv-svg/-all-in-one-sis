export type UserRole = 'admin' | 'teacher' | 'student' | 'parent'

export interface User {
  id: number
  email: string
  role: UserRole
  is_active: boolean
  last_login?: string
  person?: Person
}

export interface Person {
  id: number
  first_name: string
  last_name: string
  gender?: string
  phone?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface ApiError {
  detail: string
}
