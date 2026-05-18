'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useUser } from '@clerk/nextjs'
import { SubstanceSelector } from '@/components/onboarding/SubstanceSelector'
import { NicotineProfileStep } from '@/components/onboarding/NicotineProfileStep'
import { CannabisProfileStep } from '@/components/onboarding/CannabisProfileStep'
import { QuitDatePicker } from '@/components/onboarding/QuitDatePicker'
import { StepIndicator } from '@/components/onboarding/StepIndicator'
import { useOnboardingStore } from '@/stores/onboarding'

const MOTIVATIONS = ['Health', 'Save Money', 'Family', 'Sports Performance', 'Work Productivity', 'Relationships', 'Mental Clarity', 'Sleep Quality']

export default function OnboardingPage() {
  const router = useRouter()
  const { user } = useUser()
  const { form, setForm, nextStep, prevStep } = useOnboardingStore()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/users/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (res.ok) {
        router.push('/dashboard')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-sm p-8">
        <StepIndicator currentStep={form.step} totalSteps={6} />

        {form.step === 1 && (
          <SubstanceSelector
            value={form.substanceType}
            onChange={(v) => setForm({ substanceType: v })}
            onNext={nextStep}
          />
        )}

        {form.step === 2 && form.substanceType !== 'CANNABIS' && (
          <NicotineProfileStep
            value={form.nicotineProfile}
            onChange={(v) => setForm({ nicotineProfile: v })}
            onNext={nextStep}
            onBack={prevStep}
          />
        )}

        {form.step === 2 && form.substanceType === 'CANNABIS' && (
          <CannabisProfileStep
            value={form.cannabisProfile}
            onChange={(v) => setForm({ cannabisProfile: v })}
            onNext={nextStep}
            onBack={prevStep}
          />
        )}

        {form.step === 3 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">What's your quit goal?</h2>
            <div className="space-y-3">
              {[
                { value: 'QUIT_COMPLETELY', label: 'Quit completely', desc: 'Never use again' },
                { value: 'TOLERANCE_BREAK', label: 'Tolerance break', desc: 'Take a break and reassess' },
                { value: 'CUT_BACK', label: 'Cut back significantly', desc: 'Reduce but not eliminate' },
                { value: 'UNDECIDED', label: "I'm not sure yet", desc: 'Explore my options' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setForm({ quitGoal: opt.value as typeof form.quitGoal })}
                  className={`w-full text-left p-4 rounded-xl border-2 transition-colors ${form.quitGoal === opt.value ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'}`}
                >
                  <div className="font-semibold">{opt.label}</div>
                  <div className="text-sm text-gray-500">{opt.desc}</div>
                </button>
              ))}
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={prevStep} className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold hover:border-gray-300">Back</button>
              <button onClick={nextStep} className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700">Next</button>
            </div>
          </div>
        )}

        {form.step === 4 && (
          <QuitDatePicker
            value={form.quitDate}
            onChange={(v) => setForm({ quitDate: v })}
            onNext={nextStep}
            onBack={prevStep}
          />
        )}

        {form.step === 5 && (
          <div>
            <h2 className="text-2xl font-bold mb-2">What motivates you?</h2>
            <p className="text-gray-600 mb-6">Select all that apply (at least 1)</p>
            <div className="grid grid-cols-2 gap-3">
              {MOTIVATIONS.map((m) => {
                const selected = form.motivations.includes(m)
                return (
                  <button
                    key={m}
                    onClick={() => setForm({
                      motivations: selected
                        ? form.motivations.filter((x) => x !== m)
                        : [...form.motivations, m]
                    })}
                    className={`p-3 rounded-xl border-2 text-sm font-medium transition-colors ${selected ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 hover:border-gray-300'}`}
                  >
                    {m}
                  </button>
                )
              })}
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={prevStep} className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold">Back</button>
              <button onClick={nextStep} disabled={form.motivations.length === 0} className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold disabled:opacity-50">Next</button>
            </div>
          </div>
        )}

        {form.step === 6 && (
          <div>
            <h2 className="text-2xl font-bold mb-2">Enable notifications?</h2>
            <p className="text-gray-600 mb-6">
              ClearPath's craving predictor sends you a heads-up 30 minutes before predicted cravings — so you can prepare instead of react.
            </p>
            <div className="bg-green-50 rounded-xl p-4 mb-6">
              <div className="font-semibold text-green-800 mb-1">What you'll receive:</div>
              <ul className="text-sm text-green-700 space-y-1">
                <li>⚡ Craving prediction alerts (30 min advance warning)</li>
                <li>🔥 Streak reminders</li>
                <li>🧠 Daily CBT lesson reminders</li>
                <li>🏆 Badge achievement celebrations</li>
              </ul>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => { setForm({ notificationsEnabled: false }); handleSubmit() }}
                className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold"
              >
                Skip for now
              </button>
              <button
                onClick={() => { setForm({ notificationsEnabled: true }); handleSubmit() }}
                disabled={loading}
                className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold disabled:opacity-50"
              >
                {loading ? 'Setting up...' : 'Enable & Start →'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
