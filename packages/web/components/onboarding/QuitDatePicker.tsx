'use client'

interface Props {
  value?: string
  onChange: (v: string) => void
  onNext: () => void
  onBack: () => void
}

export function QuitDatePicker({ value, onChange, onNext, onBack }: Props) {
  const today = new Date().toISOString().split('T')[0]!

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">When did you quit (or plan to)?</h2>
      <p className="text-gray-600 mb-6">This sets your clean-time clock. You can update it anytime.</p>
      <div className="space-y-3">
        <button
          onClick={() => { onChange(new Date().toISOString()); }}
          className={`w-full p-4 rounded-xl border-2 text-left ${!value || value.startsWith(today) ? 'border-green-500 bg-green-50' : 'border-gray-200'}`}
        >
          <div className="font-semibold">Start today</div>
          <div className="text-sm text-gray-500">My quit date is today</div>
        </button>
        <div className="p-4 rounded-xl border-2 border-gray-200">
          <div className="font-semibold mb-2">Choose a date</div>
          <input
            type="date"
            max={today}
            value={value ? value.split('T')[0] : ''}
            onChange={(e) => onChange(new Date(e.target.value).toISOString())}
            className="w-full p-2 border border-gray-200 rounded-lg"
          />
        </div>
      </div>
      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="flex-1 py-3 border-2 border-gray-200 rounded-xl font-semibold">Back</button>
        <button onClick={onNext} className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold">Next</button>
      </div>
    </div>
  )
}
