"use client"

import { useCallback } from "react"
import axios, { AxiosError, AxiosRequestConfig } from "axios"

interface ApiError {
  detail: string
  code?: string
}

export function useApi() {
  const getHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }
    // Get token from localStorage or session
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      if (token) {
        headers["Authorization"] = `Bearer ${token}`
      }
    }
    return headers
  }, [])

  const api = useCallback(async <T>(
    url: string,
    options: AxiosRequestConfig = {}
  ): Promise<T> => {
    const config: AxiosRequestConfig = {
      ...options,
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    }

    try {
      const response = await axios(url, config)
      return response.data
    } catch (error) {
      const axiosError = error as AxiosError<ApiError>
      const message = axiosError.response?.data?.detail || "An error occurred"
      throw new Error(message)
    }
  }, [getHeaders()])

  const get = useCallback(<T>(url: string, options?: AxiosRequestConfig) => 
    api<T>(url, { ...options, method: "GET" }), [api])

  const post = useCallback(<T>(url: string, data?: unknown, options?: AxiosRequestConfig) =>
    api<T>(url, { ...options, method: "POST", data }), [api])

  const put = useCallback(<T>(url: string, data?: unknown, options?: AxiosRequestConfig) =>
    api<T>(url, { ...options, method: "PUT", data }), [api])

  const del = useCallback(<T>(url: string, options?: AxiosRequestConfig) =>
    api<T>(url, { ...options, method: "DELETE" }), [api])

  return { api, get, post, put, del }
}
