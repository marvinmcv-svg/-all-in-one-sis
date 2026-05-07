import { DefaultSession, DefaultUser } from 'next-auth'
import { UserRole } from './index'

declare module 'next-auth' {
  interface Session {
    user: {
      id: number
      role: UserRole
    } & DefaultSession['user']
  }

  interface User extends DefaultUser {
    role: UserRole
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    role: UserRole
  }
}
