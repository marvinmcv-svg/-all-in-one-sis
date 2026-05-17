import posthog from 'posthog-js'

export function trackEvent(event: string, properties?: Record<string, unknown>): void {
  if (typeof window === 'undefined') return
  posthog.capture(event, properties)
}

// Pre-defined events for type safety
export const track = {
  cravingLogged: (triggered: boolean, intensity: string) =>
    trackEvent('craving_logged', { triggered, intensity }),

  journalWritten: (hasMood: boolean) =>
    trackEvent('journal_written', { has_mood: hasMood }),

  cbtLessonCompleted: (week: number, lesson: number) =>
    trackEvent('cbt_lesson_completed', { week, lesson }),

  badgeEarned: (badgeKey: string) =>
    trackEvent('badge_earned', { badge_key: badgeKey }),

  communityPostCreated: () =>
    trackEvent('community_post_created'),

  aiChatSent: (messageType: string) =>
    trackEvent('ai_chat_sent', { message_type: messageType }),

  paywallViewed: () =>
    trackEvent('paywall_viewed'),

  subscriptionStarted: (tier: string) =>
    trackEvent('subscription_started', { tier }),

  onboardingCompleted: (substanceType: string) =>
    trackEvent('onboarding_completed', { substance_type: substanceType }),
}
