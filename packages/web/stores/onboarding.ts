import { create } from 'zustand'
import type { OnboardingForm } from '@clearpath/shared-types'

interface OnboardingStore {
  form: OnboardingForm
  setForm: (partial: Partial<OnboardingForm>) => void
  nextStep: () => void
  prevStep: () => void
  reset: () => void
}

const defaultForm: OnboardingForm = {
  step: 1,
  substanceType: 'NICOTINE',
  quitGoal: 'QUIT_COMPLETELY',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  motivations: [],
  notificationsEnabled: true,
}

export const useOnboardingStore = create<OnboardingStore>((set) => ({
  form: defaultForm,
  setForm: (partial) => set((state) => ({ form: { ...state.form, ...partial } })),
  nextStep: () => set((state) => ({ form: { ...state.form, step: Math.min(state.form.step + 1, 6) } })),
  prevStep: () => set((state) => ({ form: { ...state.form, step: Math.max(state.form.step - 1, 1) } })),
  reset: () => set({ form: defaultForm }),
}))
