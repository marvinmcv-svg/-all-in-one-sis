interface Props {
  value: 'NICOTINE' | 'CANNABIS' | 'BOTH'
  onChange: (v: 'NICOTINE' | 'CANNABIS' | 'BOTH') => void
  onNext: () => void
}

export function SubstanceSelector({ value, onChange, onNext }: Props) {
  const options = [
    { value: 'NICOTINE' as const, emoji: '🚭', label: 'Vaping / Nicotine', desc: 'E-cigarettes, vapes, cigarettes, pouches' },
    { value: 'CANNABIS' as const, emoji: '🌿', label: 'Cannabis / Weed', desc: 'Joints, edibles, vape carts, dabs' },
    { value: 'BOTH' as const, emoji: '🚭🌿', label: 'Both', desc: "I use nicotine AND cannabis — the dual-user path" },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">What do you want to quit?</h2>
      <p className="text-gray-600 mb-6">Select everything that applies to you.</p>
      <div className="space-y-3">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={`w-full text-left p-4 rounded-xl border-2 transition-colors ${value === opt.value ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-gray-300'}`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{opt.emoji}</span>
              <div>
                <div className="font-semibold">{opt.label}</div>
                <div className="text-sm text-gray-500">{opt.desc}</div>
              </div>
            </div>
          </button>
        ))}
      </div>
      <button onClick={onNext} className="w-full mt-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700">Next →</button>
    </div>
  )
}
