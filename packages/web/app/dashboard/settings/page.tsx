'use client'

import { useUser } from '@clerk/nextjs'
import { useState } from 'react'

export default function SettingsPage() {
  const { user } = useUser()
  const [displayName, setDisplayName] = useState(user?.fullName ?? '')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      await fetch('/api/v1/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ displayName }),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } finally {
      setSaving(false)
    }
  }

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
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Changes'}
          </button>
          {saved && <span className="text-sm text-green-600 font-medium">Saved!</span>}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold">Subscription</h2>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
          <div>
            <div className="font-medium">Free Plan</div>
            <div className="text-sm text-gray-500">3 AI messages/day, 7-day history</div>
          </div>
          <a href="/pricing" className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">
            Upgrade to Premium
          </a>
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
