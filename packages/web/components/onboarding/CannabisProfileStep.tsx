'use client'

import { useState } from 'react'

interface CannabisProfile {
  method: 'JOINT' | 'BONG' | 'PIPE' | 'EDIBLE' | 'VAPE_CART' | 'DAB' | 'OTHER'
  dailyUsageSessions: number
  costPerWeek: number
  thcPercentageAvg: number | null
  yearsUsing: number
  primaryReasons: string[]
}

interface Props {
  value?: Partial<CannabisProfile>
  onChange: (v: CannabisProfile) => void
  onNext: () => void
  onBack: () => void
}

const REASONS = ['anxiety', 'sleep', 'social', 'pain', 'creativity', 'boredom', 'habit', 'stress']

export function CannabisProfileStep({ value, onChange, onNext, onBack }: Props) {
  const [form, setForm] = useState<CannabisProfile>({
    method: 'JOINT',
    dailyUsageSessions: 2,
    costPerWeek: 50,
    thcPercentageAvg: null,
    yearsUsing: 2,
    primaryReasons: [],
    ...value,
  })

  const update = (k: keyof CannabisProfile, v: CannabisProfile[keyof CannabisProfile]) => {
    const updated = { ...form, [k]: v }
    setForm(updated)
    onChange(updated)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Your cannabis use</h2>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Method</label>
        <select value={form.method} onChange={(e) => update('method', e.target.value as CannabisProfile['method'])} className="w-full p-3 border border-gray-200 rounded-xl">
          <option value="JOINT">Joint</option>
          <option value="BONG">Bong</option>
          <option value="PIPE">Pipe</option>
          <option value="EDIBLE">Edible</option>
          <option value="VAPE_CART">Vape cart</option>
          <option value="DAB">Dab</option>
          <option value="OTHER">Other</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Sessions per day</label>
        <input type="number" min={1} value={form.dailyUsageSessions} onChange={(e) => update('dailyUsageSessions', parseInt(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Weekly cost ($)</label>
        <input type="number" min={0} value={form.costPerWeek} onChange={(e) => update('costPerWeek', parseFloat(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Why do you use? (select all that apply)</label>
        <div className="flex flex-wrap gap-2">
          {REASONS.map((r) => (
            <button
              key={r}
              onClick={() => update('primaryReasons', form.primaryReasons.includes(r) ? form.primaryReasons.filter((x) => x !== r) : [...form.primaryReasons, r])}
              className={`px-3 py-1 rounded-full text-sm border-2 ${form.primaryReasons.includes(r) ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 text-gray-600'}`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
      <div className="flex gap-3">
        <button onClick={onBack} className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold">Back</button>
        <button onClick={onNext} className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold">Next</button>
      </div>
    </div>
  )
}
