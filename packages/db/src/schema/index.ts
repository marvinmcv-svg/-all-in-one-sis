import {
  pgTable, uuid, text, integer, real, boolean,
  timestamp, jsonb, index, uniqueIndex, pgEnum,
} from 'drizzle-orm/pg-core'
import { relations } from 'drizzle-orm'

// ── ENUMS ──────────────────────────────────────────────────────
export const substanceTypeEnum = pgEnum('substance_type', ['NICOTINE', 'CANNABIS', 'BOTH'])
export const nicotineMethodEnum = pgEnum('nicotine_method', ['VAPE', 'CIGARETTE', 'CIGAR', 'NICOTINE_POUCH', 'OTHER'])
export const cannabisMethodEnum = pgEnum('cannabis_method', ['JOINT', 'BONG', 'PIPE', 'EDIBLE', 'VAPE_CART', 'DAB', 'OTHER'])
export const quitGoalEnum = pgEnum('quit_goal', ['QUIT_COMPLETELY', 'TOLERANCE_BREAK', 'CUT_BACK', 'UNDECIDED'])
export const cravingIntensityEnum = pgEnum('craving_intensity', ['LOW', 'MEDIUM', 'HIGH', 'OVERWHELMING'])
export const subscriptionTierEnum = pgEnum('subscription_tier', ['FREE', 'PREMIUM', 'ENTERPRISE', 'CLINICAL'])
export const badgeCategoryEnum = pgEnum('badge_category', ['TIME_CLEAN', 'MONEY_SAVED', 'CRAVINGS_BEATEN', 'CBT_PROGRESS', 'COMMUNITY', 'STREAK', 'MILESTONE'])
export const messageTypeEnum = pgEnum('message_type', ['COACHING', 'CRISIS', 'CBT', 'GENERAL'])
export const exerciseTypeEnum = pgEnum('exercise_type', ['THOUGHT_RECORD', 'BEHAVIORAL_ACTIVATION', 'EXPOSURE', 'RELAXATION', 'MINDFULNESS', 'REFLECTION'])

// ── USERS ──────────────────────────────────────────────────────
export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  clerkId: text('clerk_id').notNull().unique(),
  email: text('email').notNull().unique(),
  displayName: text('display_name').notNull(),
  avatarUrl: text('avatar_url'),
  substanceType: substanceTypeEnum('substance_type').notNull().default('NICOTINE'),
  quitGoal: quitGoalEnum('quit_goal').notNull().default('QUIT_COMPLETELY'),
  quitDate: timestamp('quit_date', { withTimezone: true }),
  subscriptionTier: subscriptionTierEnum('subscription_tier').notNull().default('FREE'),
  timezone: text('timezone').notNull().default('America/New_York'),
  notificationsEnabled: boolean('notifications_enabled').notNull().default(true),
  expoPushToken: text('expo_push_token'),
  onboardingCompleted: boolean('onboarding_completed').notNull().default(false),
  longestStreakDays: integer('longest_streak_days').notNull().default(0),
  totalBadgesEarned: integer('total_badges_earned').notNull().default(0),
  aiMessagesUsedToday: integer('ai_messages_used_today').notNull().default(0),
  aiMessagesResetAt: timestamp('ai_messages_reset_at', { withTimezone: true }),
  anonymousAlias: text('anonymous_alias'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  clerkIdx: uniqueIndex('users_clerk_id_idx').on(t.clerkId),
  emailIdx: uniqueIndex('users_email_idx').on(t.email),
}))

// ── NICOTINE PROFILES ──────────────────────────────────────────
export const nicotineProfiles = pgTable('nicotine_profiles', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  method: nicotineMethodEnum('method').notNull().default('VAPE'),
  dailyUsageAmount: real('daily_usage_amount').notNull(),
  nicotineStrengthMg: real('nicotine_strength_mg'),
  costPerUnit: real('cost_per_unit').notNull(),
  yearsUsing: integer('years_using').notNull().default(0),
  previousQuitAttempts: integer('previous_quit_attempts').notNull().default(0),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('nicotine_profiles_user_id_idx').on(t.userId),
}))

// ── CANNABIS PROFILES ──────────────────────────────────────────
export const cannabisProfiles = pgTable('cannabis_profiles', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  method: cannabisMethodEnum('method').notNull().default('JOINT'),
  dailyUsageSessions: integer('daily_usage_sessions').notNull().default(1),
  costPerWeek: real('cost_per_week').notNull(),
  thcPercentageAvg: real('thc_percentage_avg'),
  yearsUsing: integer('years_using').notNull().default(0),
  primaryReasons: jsonb('primary_reasons').$type<string[]>().notNull().default([]),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('cannabis_profiles_user_id_idx').on(t.userId),
}))

// ── CRAVING LOGS ───────────────────────────────────────────────
export const cravingLogs = pgTable('craving_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  substanceType: substanceTypeEnum('substance_type').notNull(),
  intensity: cravingIntensityEnum('intensity').notNull(),
  triggered: boolean('triggered').notNull().default(false),
  triggerTags: jsonb('trigger_tags').$type<string[]>().notNull().default([]),
  mood: integer('mood').notNull(),
  location: text('location'),
  copingUsed: text('coping_used'),
  notes: text('notes'),
  loggedAt: timestamp('logged_at', { withTimezone: true }).notNull().defaultNow(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('craving_logs_user_id_idx').on(t.userId),
  loggedAtIdx: index('craving_logs_logged_at_idx').on(t.loggedAt),
  userLoggedAtIdx: index('craving_logs_user_logged_at_idx').on(t.userId, t.loggedAt),
}))

// ── USAGE LOGS ─────────────────────────────────────────────────
export const usageLogs = pgTable('usage_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  substanceType: substanceTypeEnum('substance_type').notNull(),
  amount: real('amount').notNull(),
  mood: integer('mood').notNull(),
  triggerTags: jsonb('trigger_tags').$type<string[]>().notNull().default([]),
  notes: text('notes'),
  loggedAt: timestamp('logged_at', { withTimezone: true }).notNull().defaultNow(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('usage_logs_user_id_idx').on(t.userId),
  loggedAtIdx: index('usage_logs_logged_at_idx').on(t.loggedAt),
}))

// ── JOURNAL ENTRIES ────────────────────────────────────────────
export const journalEntries = pgTable('journal_entries', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  title: text('title'),
  content: text('content').notNull(),
  mood: integer('mood').notNull(),
  substanceType: substanceTypeEnum('substance_type'),
  audioUrl: text('audio_url'),
  transcription: text('transcription'),
  embeddingJson: jsonb('embedding_json').$type<number[]>(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('journal_entries_user_id_idx').on(t.userId),
}))

// ── CBT MODULES ────────────────────────────────────────────────
export const cbtModules = pgTable('cbt_modules', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  weekNumber: integer('week_number').notNull(),
  lessonNumber: integer('lesson_number').notNull(),
  title: text('title').notNull(),
  content: text('content').notNull(),
  exerciseType: exerciseTypeEnum('exercise_type').notNull(),
  completedAt: timestamp('completed_at', { withTimezone: true }),
  responseText: text('response_text'),
  aiFeedback: text('ai_feedback'),
}, (t) => ({
  userIdx: index('cbt_modules_user_id_idx').on(t.userId),
  weekLessonIdx: uniqueIndex('cbt_modules_user_week_lesson_idx').on(t.userId, t.weekNumber, t.lessonNumber),
}))

// ── BADGES ─────────────────────────────────────────────────────
export const badges = pgTable('badges', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  badgeKey: text('badge_key').notNull(),
  category: badgeCategoryEnum('category').notNull(),
  title: text('title').notNull(),
  description: text('description').notNull(),
  iconEmoji: text('icon_emoji').notNull(),
  earnedAt: timestamp('earned_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('badges_user_id_idx').on(t.userId),
  uniqueBadgeIdx: uniqueIndex('badges_user_badge_key_idx').on(t.userId, t.badgeKey),
}))

// ── AI MESSAGES ────────────────────────────────────────────────
export const aiMessages = pgTable('ai_messages', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  role: text('role').$type<'user' | 'assistant'>().notNull(),
  content: text('content').notNull(),
  sessionId: text('session_id').notNull(),
  messageType: messageTypeEnum('message_type').notNull().default('COACHING'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('ai_messages_user_id_idx').on(t.userId),
  sessionIdx: index('ai_messages_session_id_idx').on(t.sessionId),
}))

// ── CRAVING PREDICTIONS ────────────────────────────────────────
export const cravingPredictions = pgTable('craving_predictions', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  substanceType: substanceTypeEnum('substance_type').notNull(),
  predictedAt: timestamp('predicted_at', { withTimezone: true }).notNull(),
  confidence: real('confidence').notNull(),
  triggerFactors: jsonb('trigger_factors').$type<string[]>().notNull().default([]),
  notificationSentAt: timestamp('notification_sent_at', { withTimezone: true }),
  wasAccurate: boolean('was_accurate'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  userIdx: index('craving_predictions_user_id_idx').on(t.userId),
  predictedAtIdx: index('craving_predictions_predicted_at_idx').on(t.predictedAt),
}))

// ── COMMUNITY POSTS ────────────────────────────────────────────
export const communityPosts = pgTable('community_posts', {
  id: uuid('id').primaryKey().defaultRandom(),
  authorId: uuid('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  anonymousAlias: text('anonymous_alias').notNull(),
  title: text('title').notNull(),
  content: text('content').notNull(),
  substanceTags: jsonb('substance_tags').$type<string[]>().notNull().default([]),
  likes: integer('likes').notNull().default(0),
  commentCount: integer('comment_count').notNull().default(0),
  isPinned: boolean('is_pinned').notNull().default(false),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  authorIdx: index('community_posts_author_id_idx').on(t.authorId),
  createdAtIdx: index('community_posts_created_at_idx').on(t.createdAt),
}))

// ── COMMUNITY COMMENTS ─────────────────────────────────────────
export const communityComments = pgTable('community_comments', {
  id: uuid('id').primaryKey().defaultRandom(),
  postId: uuid('post_id').notNull().references(() => communityPosts.id, { onDelete: 'cascade' }),
  authorId: uuid('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  anonymousAlias: text('anonymous_alias').notNull(),
  content: text('content').notNull(),
  likes: integer('likes').notNull().default(0),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (t) => ({
  postIdx: index('community_comments_post_id_idx').on(t.postId),
}))

// ── HEALTH MILESTONES ──────────────────────────────────────────
export const healthMilestones = pgTable('health_milestones', {
  id: uuid('id').primaryKey().defaultRandom(),
  substanceType: substanceTypeEnum('substance_type').notNull(),
  targetDays: real('target_days').notNull(),
  title: text('title').notNull(),
  description: text('description').notNull(),
  bodySystem: text('body_system').notNull(),
  iconEmoji: text('icon_emoji').notNull(),
  sourceUrl: text('source_url'),
})

// ── PUSH NOTIFICATION LOGS ─────────────────────────────────────
export const pushNotificationLogs = pgTable('push_notification_logs', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  type: text('type').notNull(),
  title: text('title').notNull(),
  body: text('body').notNull(),
  sentAt: timestamp('sent_at', { withTimezone: true }).notNull().defaultNow(),
  openedAt: timestamp('opened_at', { withTimezone: true }),
  data: jsonb('data'),
})

// ── RELATIONS ─────────────────────────────────────────────────
export const usersRelations = relations(users, ({ one, many }) => ({
  nicotineProfile: one(nicotineProfiles, { fields: [users.id], references: [nicotineProfiles.userId] }),
  cannabisProfile: one(cannabisProfiles, { fields: [users.id], references: [cannabisProfiles.userId] }),
  cravingLogs: many(cravingLogs),
  usageLogs: many(usageLogs),
  journalEntries: many(journalEntries),
  cbtModules: many(cbtModules),
  badges: many(badges),
  aiMessages: many(aiMessages),
  cravingPredictions: many(cravingPredictions),
  communityPosts: many(communityPosts),
}))

export const nicotineProfilesRelations = relations(nicotineProfiles, ({ one }) => ({
  user: one(users, { fields: [nicotineProfiles.userId], references: [users.id] }),
}))

export const cannabisProfilesRelations = relations(cannabisProfiles, ({ one }) => ({
  user: one(users, { fields: [cannabisProfiles.userId], references: [users.id] }),
}))

export const cravingLogsRelations = relations(cravingLogs, ({ one }) => ({
  user: one(users, { fields: [cravingLogs.userId], references: [users.id] }),
}))

export const usageLogsRelations = relations(usageLogs, ({ one }) => ({
  user: one(users, { fields: [usageLogs.userId], references: [users.id] }),
}))

export const journalEntriesRelations = relations(journalEntries, ({ one }) => ({
  user: one(users, { fields: [journalEntries.userId], references: [users.id] }),
}))

export const cbtModulesRelations = relations(cbtModules, ({ one }) => ({
  user: one(users, { fields: [cbtModules.userId], references: [users.id] }),
}))

export const badgesRelations = relations(badges, ({ one }) => ({
  user: one(users, { fields: [badges.userId], references: [users.id] }),
}))

export const aiMessagesRelations = relations(aiMessages, ({ one }) => ({
  user: one(users, { fields: [aiMessages.userId], references: [users.id] }),
}))

export const cravingPredictionsRelations = relations(cravingPredictions, ({ one }) => ({
  user: one(users, { fields: [cravingPredictions.userId], references: [users.id] }),
}))

export const communityPostsRelations = relations(communityPosts, ({ one, many }) => ({
  author: one(users, { fields: [communityPosts.authorId], references: [users.id] }),
  comments: many(communityComments),
}))

export const communityCommentsRelations = relations(communityComments, ({ one }) => ({
  post: one(communityPosts, { fields: [communityComments.postId], references: [communityPosts.id] }),
  author: one(users, { fields: [communityComments.authorId], references: [users.id] }),
}))
