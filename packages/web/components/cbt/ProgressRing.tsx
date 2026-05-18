interface Props {
  progress: number
  size?: number
}

export function ProgressRing({ progress, size = 48 }: Props) {
  const r = (size - 8) / 2
  const circumference = 2 * Math.PI * r
  const offset = circumference - (progress / 100) * circumference

  return (
    <svg width={size} height={size}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e5e7eb" strokeWidth={4} />
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none" stroke="#22c55e" strokeWidth={4}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize={size * 0.22} fill="#22c55e" fontWeight="600">
        {progress}%
      </text>
    </svg>
  )
}
