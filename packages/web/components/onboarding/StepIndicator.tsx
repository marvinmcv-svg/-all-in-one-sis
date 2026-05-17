interface Props {
  currentStep: number
  totalSteps: number
}

export function StepIndicator({ currentStep, totalSteps }: Props) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: totalSteps }, (_, i) => (
        <div
          key={i}
          className={`h-2 rounded-full flex-1 transition-all ${i + 1 <= currentStep ? 'bg-green-500' : 'bg-gray-200'}`}
        />
      ))}
    </div>
  )
}
