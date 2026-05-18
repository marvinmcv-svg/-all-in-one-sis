'use client'

import { useState } from 'react'
import { CravingLogForm } from '@/components/track/CravingLogForm'

export function QuickLogModal() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="px-4 py-2 bg-red-500 text-white rounded-xl font-medium hover:bg-red-600"
      >
        ⚡ Log Craving
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Log Craving</h2>
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <CravingLogForm onSuccess={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  )
}
