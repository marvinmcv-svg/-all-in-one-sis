'use client'

import { useState } from 'react'

interface NicotineProfile {
  method: 'VAPE' | 'CIGARETTE' | 'CIGAR' | 'NICOTINE_POUCH' | 'OTHER'
  dailyUsageAmount: number
  nicotineStrengthMg: number | null
  costPerUnit: number
  yearsUsing: number
  previousQuitAttempts: number
}

interface Props {
  value?: Partial<NicotineProfile>
  onChange: (v: NicotineProfile) => void
  onNext: () => void
  onBack: () => void
}

export function NicotineProfileStep({ value, onChange, onNext, onBack }: Props) {
  const [form, setForm] = useState<NicotineProfile>({
    method: 'VAPE',
    dailyUsageAmount: 100,
    nicotineStrengthMg: null,
    costPerUnit: 15,
    yearsUsing: 2,
    previousQuitAttempts: 0,
    ...value,
  })

  const update = (k: keyof NicotineProfile, v: NicotineProfile[keyof NicotineProfile]) => {
    const updated = { ...form, [k]: v }
    setForm(updated)
    onChange(updated)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Your nicotine use</h2>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Method</label>
        <select value={form.method} onChange={(e) => update('method', e.target.value as NicotineProfile['method'])} className="w-full p-3 border border-gray-200 rounded-xl">
          <option value="VAPE">Vape / E-cigarette</option>
          <option value="CIGARETTE">Cigarettes</option>
          <option value="CIGAR">Cigars</option>
          <option value="NICOTINE_POUCH">Nicotine pouch</option>
          <option value="OTHER">Other</option>
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Puffs per day (approx)</label>
        <input type="number" min={1} value={form.dailyUsageAmount} onChange={(e) => update('dailyUsageAmount', parseInt(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Cost per pod/pack ($)</label>
        <input type="number" min={0} step={0.01} value={form.costPerUnit} onChange={(e) => update('costPerUnit', parseFloat(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Years using</label>
        <input type="number" min={0} value={form.yearsUsing} onChange={(e) => update('yearsUsing', parseInt(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Previous quit attempts</label>
        <input type="number" min={0} value={form.previousQuitAttempts} onChange={(e) => update('previousQuitAttempts', parseInt(e.target.value))} className="w-full p-3 border border-gray-200 rounded-xl" />
      </div>
      <div className="flex gap-3">
        <button onClick={onBack} className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold">Back</button>
        <button onClick={onNext} className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold">Next</button>
      </div>
    </div>
  )
}
