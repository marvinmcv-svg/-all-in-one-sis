import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import { PostHogProvider } from '@/components/PostHogProvider'
import './globals.css'

export const metadata: Metadata = {
  title: 'ClearPath — Quit Vaping & Cannabis',
  description: 'The first AI-powered dual-substance recovery platform for vaping & cannabis',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body><PostHogProvider>{children}</PostHogProvider></body>
      </html>
    </ClerkProvider>
  )
}
