export interface NotificationTemplate {
  title: string
  body: string
  data: Record<string, string>
}

export function cravingPredictionTemplate(name: string): NotificationTemplate {
  return {
    title: `⚡ Heads up, ${name}`,
    body: "Based on your patterns, you might be hit with a craving in about 30 minutes. You've got this.",
    data: { type: 'CRAVING_PREDICTION', screen: 'quick-log' }
  }
}

export function streakAlertTemplate(days: number): NotificationTemplate {
  return {
    title: `🔥 ${days}-day streak on the line`,
    body: `You haven't logged today — don't break your ${days}-day streak! Tap to log.`,
    data: { type: 'STREAK_ALERT', screen: 'track' }
  }
}

export function badgeEarnedTemplate(emoji: string, title: string, description: string, key: string): NotificationTemplate {
  return {
    title: `${emoji} New Badge: ${title}`,
    body: description,
    data: { type: 'BADGE_EARNED', screen: 'badges', badgeKey: key }
  }
}

export function cbtReminderTemplate(week: number, day: number, lessonTitle: string): NotificationTemplate {
  return {
    title: '🧠 Your daily lesson is waiting',
    body: `Week ${week}, Day ${day}: ${lessonTitle}. Takes 5 minutes.`,
    data: { type: 'CBT_REMINDER', screen: 'cbt' }
  }
}

export function milestoneReachedTemplate(milestoneTitle: string, milestoneDescription: string): NotificationTemplate {
  return {
    title: `🏆 Health milestone: ${milestoneTitle}`,
    body: milestoneDescription,
    data: { type: 'MILESTONE', screen: 'dashboard' }
  }
}

export function weeklyInsightTemplate(insight: string): NotificationTemplate {
  return {
    title: '📊 Your week in review',
    body: insight,
    data: { type: 'WEEKLY_INSIGHT', screen: 'dashboard' }
  }
}
