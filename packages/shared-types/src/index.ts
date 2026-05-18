import { z } from 'zod'

// ── ENUMS ──────────────────────────────────────────────────────
export const SubstanceType = z.enum(['NICOTINE', 'CANNABIS', 'BOTH'])
export type SubstanceType = z.infer<typeof SubstanceType>

export const NicotineMethod = z.enum(['VAPE', 'CIGARETTE', 'CIGAR', 'NICOTINE_POUCH', 'OTHER'])
export type NicotineMethod = z.infer<typeof NicotineMethod>

export const CannabisMethod = z.enum(['JOINT', 'BONG', 'PIPE', 'EDIBLE', 'VAPE_CART', 'DAB', 'OTHER'])
export type CannabisMethod = z.infer<typeof CannabisMethod>

export const QuitGoal = z.enum(['QUIT_COMPLETELY', 'TOLERANCE_BREAK', 'CUT_BACK', 'UNDECIDED'])
export type QuitGoal = z.infer<typeof QuitGoal>

export const CravingIntensity = z.enum(['LOW', 'MEDIUM', 'HIGH', 'OVERWHELMING'])
export type CravingIntensity = z.infer<typeof CravingIntensity>

export const MoodScore = z.number().int().min(1).max(10)

export const SubscriptionTier = z.enum(['FREE', 'PREMIUM', 'ENTERPRISE', 'CLINICAL'])
export type SubscriptionTier = z.infer<typeof SubscriptionTier>

export const BadgeCategory = z.enum([
  'TIME_CLEAN', 'MONEY_SAVED', 'CRAVINGS_BEATEN',
  'CBT_PROGRESS', 'COMMUNITY', 'STREAK', 'MILESTONE'
])
export type BadgeCategory = z.infer<typeof BadgeCategory>

// ── USER PROFILE ───────────────────────────────────────────────
export const UserProfileSchema = z.object({
  id: z.string().uuid(),
  clerkId: z.string(),
  email: z.string().email(),
  displayName: z.string().min(1).max(50),
  avatarUrl: z.string().url().nullable(),
  substanceType: SubstanceType,
  quitGoal: QuitGoal,
  quitDate: z.string().datetime().nullable(),
  subscriptionTier: SubscriptionTier,
  timezone: z.string(),
  notificationsEnabled: z.boolean(),
  onboardingCompleted: z.boolean(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
})
export type UserProfile = z.infer<typeof UserProfileSchema>

// ── NICOTINE PROFILE ───────────────────────────────────────────
export const NicotineProfileSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  method: NicotineMethod,
  dailyUsageAmount: z.number().positive(),
  nicotineStrengthMg: z.number().nullable(),
  costPerUnit: z.number().positive(),
  yearsUsing: z.number().int().min(0),
  previousQuitAttempts: z.number().int().min(0),
  createdAt: z.string().datetime(),
})
export type NicotineProfile = z.infer<typeof NicotineProfileSchema>

// ── CANNABIS PROFILE ───────────────────────────────────────────
export const CannabisProfileSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  method: CannabisMethod,
  dailyUsageSessions: z.number().int().positive(),
  costPerWeek: z.number().positive(),
  thcPercentageAvg: z.number().nullable(),
  yearsUsing: z.number().int().min(0),
  primaryReasons: z.array(z.string()).max(5),
  createdAt: z.string().datetime(),
})
export type CannabisProfile = z.infer<typeof CannabisProfileSchema>

// ── CRAVING LOG ────────────────────────────────────────────────
export const CravingLogSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  substanceType: SubstanceType,
  intensity: CravingIntensity,
  triggered: z.boolean(),
  triggerTags: z.array(z.string()).max(10),
  mood: MoodScore,
  location: z.string().nullable(),
  copingUsed: z.string().nullable(),
  notes: z.string().max(500).nullable(),
  loggedAt: z.string().datetime(),
  createdAt: z.string().datetime(),
})
export type CravingLog = z.infer<typeof CravingLogSchema>

// ── USAGE LOG ──────────────────────────────────────────────────
export const UsageLogSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  substanceType: SubstanceType,
  amount: z.number().positive(),
  mood: MoodScore,
  triggerTags: z.array(z.string()).max(10),
  notes: z.string().max(500).nullable(),
  loggedAt: z.string().datetime(),
  createdAt: z.string().datetime(),
})
export type UsageLog = z.infer<typeof UsageLogSchema>

// ── JOURNAL ENTRY ──────────────────────────────────────────────
export const JournalEntrySchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  title: z.string().max(100).nullable(),
  content: z.string().max(5000),
  mood: MoodScore,
  substanceType: SubstanceType.nullable(),
  audioUrl: z.string().url().nullable(),
  transcription: z.string().nullable(),
  embeddingVector: z.array(z.number()).nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
})
export type JournalEntry = z.infer<typeof JournalEntrySchema>

// ── CBT MODULE ─────────────────────────────────────────────────
export const CBTModuleSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  weekNumber: z.number().int().min(1).max(6),
  lessonNumber: z.number().int().min(1).max(7),
  title: z.string(),
  content: z.string(),
  exerciseType: z.enum(['THOUGHT_RECORD', 'BEHAVIORAL_ACTIVATION', 'EXPOSURE', 'RELAXATION', 'MINDFULNESS', 'REFLECTION']),
  completedAt: z.string().datetime().nullable(),
  responseText: z.string().nullable(),
  aiFeedback: z.string().nullable(),
})
export type CBTModule = z.infer<typeof CBTModuleSchema>

// ── BADGE ──────────────────────────────────────────────────────
export const BadgeSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  badgeKey: z.string(),
  category: BadgeCategory,
  title: z.string(),
  description: z.string(),
  iconEmoji: z.string(),
  earnedAt: z.string().datetime(),
})
export type Badge = z.infer<typeof BadgeSchema>

// ── AI COACH MESSAGE ───────────────────────────────────────────
export const AIMessageSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  sessionId: z.string(),
  messageType: z.enum(['COACHING', 'CRISIS', 'CBT', 'GENERAL']),
  createdAt: z.string().datetime(),
})
export type AIMessage = z.infer<typeof AIMessageSchema>

// ── CRAVING PREDICTION ─────────────────────────────────────────
export const CravingPredictionSchema = z.object({
  id: z.string().uuid(),
  userId: z.string().uuid(),
  substanceType: SubstanceType,
  predictedAt: z.string().datetime(),
  confidence: z.number().min(0).max(1),
  triggerFactors: z.array(z.string()),
  notificationSentAt: z.string().datetime().nullable(),
  wasAccurate: z.boolean().nullable(),
})
export type CravingPrediction = z.infer<typeof CravingPredictionSchema>

// ── COMMUNITY POST ─────────────────────────────────────────────
export const CommunityPostSchema = z.object({
  id: z.string().uuid(),
  authorId: z.string().uuid(),
  anonymousAlias: z.string(),
  title: z.string().max(150),
  content: z.string().max(2000),
  substanceTags: z.array(SubstanceType),
  likes: z.number().int().min(0),
  commentCount: z.number().int().min(0),
  isPinned: z.boolean(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
})
export type CommunityPost = z.infer<typeof CommunityPostSchema>

// ── API RESPONSE SHAPES ────────────────────────────────────────
export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.nullable(),
    error: z.string().nullable(),
    meta: z.object({
      timestamp: z.string().datetime(),
      requestId: z.string(),
    }).optional(),
  })

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    success: z.literal(true),
    data: z.array(itemSchema),
    pagination: z.object({
      page: z.number().int().positive(),
      limit: z.number().int().positive(),
      total: z.number().int().min(0),
      hasMore: z.boolean(),
    }),
  })

// ── DASHBOARD STATS ────────────────────────────────────────────
export const DashboardStatsSchema = z.object({
  userId: z.string().uuid(),
  substanceType: SubstanceType,
  cleanSinceDatetime: z.string().datetime().nullable(),
  secondsClean: z.number().int().min(0),
  daysClean: z.number().int().min(0),
  longestStreakDays: z.number().int().min(0),
  currentStreakDays: z.number().int().min(0),
  moneySavedCents: z.number().int().min(0),
  projectedYearlySavingsCents: z.number().int().min(0),
  healthMilestonesCurrent: z.array(z.object({
    key: z.string(),
    title: z.string(),
    description: z.string(),
    achievedAt: z.string().datetime().nullable(),
    targetDays: z.number().int(),
  })),
  cravingsBeatThisWeek: z.number().int().min(0),
  avgMoodThisWeek: z.number().min(1).max(10).nullable(),
  badgesEarned: z.number().int().min(0),
})
export type DashboardStats = z.infer<typeof DashboardStatsSchema>

// ── ONBOARDING FORM ────────────────────────────────────────────
export const OnboardingFormSchema = z.object({
  step: z.number().int().min(1).max(6),
  substanceType: SubstanceType,
  quitGoal: QuitGoal,
  quitDate: z.string().datetime().optional(),
  timezone: z.string(),
  nicotineProfile: NicotineProfileSchema.omit({ id: true, userId: true, createdAt: true }).optional(),
  cannabisProfile: CannabisProfileSchema.omit({ id: true, userId: true, createdAt: true }).optional(),
  motivations: z.array(z.string()).min(1).max(5),
  notificationsEnabled: z.boolean(),
})
export type OnboardingForm = z.infer<typeof OnboardingFormSchema>
