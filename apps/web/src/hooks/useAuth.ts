"use client"

import { useSession, signIn, signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useState, useCallback } from "react"

interface LoginCredentials {
  email: string
  password: string
}

export function useAuth() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = useCallback(async ({ email, password }: LoginCredentials) => {
    setLoading(true)
    setError(null)
    try {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      })
      if (result?.error) {
        setError("Invalid email or password")
        return false
      }
      router.push("/")
      return true
    } catch (err) {
      setError("An error occurred during login")
      return false
    } finally {
      setLoading(false)
    }
  }, [router])

  const logout = useCallback(async () => {
    setLoading(true)
    try {
      await signOut({ redirect: false })
      router.push("/login")
    } finally {
      setLoading(false)
    }
  }, [router])

  return {
    user: session?.user,
    isAuthenticated: !!session?.user,
    isLoading: status === "loading",
    login,
    logout,
    loading,
    error,
  }
}
