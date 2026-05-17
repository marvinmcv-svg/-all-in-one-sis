'use client'

import { useUser } from '@clerk/nextjs'
import { useState } from 'react'

export default function SettingsPage() {
  const { user } = useUser()
  const [saved, setSaved] = useState(false)

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold">Profile</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <div className="p-3 bg-gray-50 rounded-lg text-gray-600">{user?.primaryEmailAddress?.emailAddress}</div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
          <input
            defaultValue={user?.fullName ?? ''}
            className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold">Subscription</h2>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
          <div>
            <div className="font-medium">Free Plan</div>
            <div className="text-sm text-gray-500">3 AI messages/day, 7-day history</div>
          </div>
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">
            Upgrade to Premium
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold text-red-600">Danger Zone</h2>
        <button className="px-4 py-2 border-2 border-red-200 text-red-600 rounded-lg text-sm hover:bg-red-50">
          Delete Account
        </button>
      </div>
    </div>
  )
}
