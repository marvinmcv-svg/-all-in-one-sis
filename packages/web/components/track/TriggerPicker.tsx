'use client'

import { TRIGGER_TAGS } from '@/lib/constants'

interface Props {
  selected: string[]
  onChange: (tags: string[]) => void
}

export function TriggerPicker({ selected, onChange }: Props) {
  const toggle = (tag: string) => {
    onChange(selected.includes(tag) ? selected.filter((t) => t !== tag) : [...selected, tag])
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Triggers</label>
      <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
        {TRIGGER_TAGS.map((tag) => (
          <button
            key={tag}
            onClick={() => toggle(tag)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${selected.includes(tag) ? 'bg-red-100 text-red-700 border border-red-300' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  )
}
