import { Router } from 'express'
import { db, cbtModules } from '@clearpath/db'
import { eq, and } from 'drizzle-orm'
import { requireUser } from '../middleware/auth.js'
import xss from 'xss'
import { generateCBTFeedback } from '@clearpath/ai-pipeline'
import { badgeEvaluatorQueue } from '../jobs/index.js'

export const cbtRouter = Router()
cbtRouter.use(requireUser)

const CBT_CURRICULUM: Array<{ weekNumber: number; lessonNumber: number; title: string; content: string; exerciseType: 'THOUGHT_RECORD' | 'BEHAVIORAL_ACTIVATION' | 'EXPOSURE' | 'RELAXATION' | 'MINDFULNESS' | 'REFLECTION' }> = [
  // Week 1
  { weekNumber: 1, lessonNumber: 1, title: 'Welcome — The Science of Your Addiction', content: 'Understanding how nicotine and cannabis affect your brain\'s reward system. Your habit isn\'t a moral failure — it\'s a learned neurological pattern that can be unlearned.', exerciseType: 'REFLECTION' },
  { weekNumber: 1, lessonNumber: 2, title: 'Craving Anatomy — What Happens in 90 Seconds', content: 'A craving peaks at 90 seconds and then fades. Your exercise today: time a craving and observe it passing without acting on it.', exerciseType: 'MINDFULNESS' },
  { weekNumber: 1, lessonNumber: 3, title: 'Trigger Mapping', content: 'Identify your top 5 personal triggers. Log them in detail: time, place, emotion, what preceded the urge.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 1, lessonNumber: 4, title: 'Urge Surfing', content: 'Ride the wave of a craving without wiping out. Imagine the craving as an ocean wave — it builds, peaks, and passes.', exerciseType: 'MINDFULNESS' },
  { weekNumber: 1, lessonNumber: 5, title: 'Values Clarification', content: 'Why do YOU want to quit? Write down your top 3 deeply personal reasons. These become your anchor when cravings hit.', exerciseType: 'REFLECTION' },
  { weekNumber: 1, lessonNumber: 6, title: 'Emergency Toolkit', content: 'Build your personalized craving interruption plan: 3 immediate distractions, 2 people to call, 1 breathing technique.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 1, lessonNumber: 7, title: 'Week 1 Reflection', content: 'Review your progress. What triggers did you identify? What coping strategies worked best? Rate your confidence from 1-10.', exerciseType: 'REFLECTION' },
  // Week 2
  { weekNumber: 2, lessonNumber: 1, title: 'Introduction to Automatic Thoughts', content: 'Automatic thoughts are the instant, unquestioned thoughts that arise before a craving. Today, start noticing them without judgment.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 2, lessonNumber: 2, title: 'Thought Record Exercise', content: 'Three-column exercise: Situation → Automatic Thought → Emotion. Complete at least one full thought record today.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 2, lessonNumber: 3, title: 'Cognitive Distortions in Addiction', content: 'Learn the 5 most common distortions: all-or-nothing thinking, catastrophizing, mind reading, emotional reasoning, and should statements.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 2, lessonNumber: 4, title: 'Challenging the "I Deserve This" Thought', content: 'This is the #1 relapse thought. Today\'s exercise: write 3 alternative thoughts that honor your needs without using.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 2, lessonNumber: 5, title: 'Behavioral Activation — Replace the Ritual', content: 'Identify the ritual surrounding your use (e.g., stepping outside, rolling a joint). Create an alternative ritual that meets the same need.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 2, lessonNumber: 6, title: 'Social Triggers Deep Dive', content: 'Examine how social situations trigger use. Develop specific response plans for your top 3 social trigger scenarios.', exerciseType: 'EXPOSURE' },
  { weekNumber: 2, lessonNumber: 7, title: 'Week 2 Reflection', content: 'Review your thought records. What patterns do you notice? Which distortions show up most often for you?', exerciseType: 'REFLECTION' },
  // Week 3
  { weekNumber: 3, lessonNumber: 1, title: 'Emotions as Triggers', content: 'Map your emotional triggers. Which emotions most reliably precede cravings? Anxiety? Boredom? Excitement?', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 3, lessonNumber: 2, title: 'Box Breathing Technique', content: 'Box breathing (4-4-4-4): Inhale 4 counts, hold 4, exhale 4, hold 4. Practice 3 rounds now.', exerciseType: 'RELAXATION' },
  { weekNumber: 3, lessonNumber: 3, title: 'Progressive Muscle Relaxation', content: 'Tense and release each muscle group systematically. This counters the physical anxiety that accompanies cravings.', exerciseType: 'RELAXATION' },
  { weekNumber: 3, lessonNumber: 4, title: 'Mindful Body Scan', content: 'A 10-minute body scan meditation to develop interoceptive awareness — knowing what\'s happening in your body before you reach for a substance.', exerciseType: 'MINDFULNESS' },
  { weekNumber: 3, lessonNumber: 5, title: 'Anger & Frustration Management', content: 'Anger is a high-relapse-risk emotion. Develop your anger de-escalation toolkit: physical release, cognitive reframe, time-out protocol.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 3, lessonNumber: 6, title: 'Loneliness & Social Use', content: 'For many, substance use is deeply social. Explore alternative connection strategies that don\'t involve using.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 3, lessonNumber: 7, title: 'Week 3 Reflection', content: 'Which relaxation technique worked best for you? How has your emotional awareness changed since Week 1?', exerciseType: 'REFLECTION' },
  // Week 4
  { weekNumber: 4, lessonNumber: 1, title: 'Lapse vs. Relapse — The Critical Difference', content: 'A lapse is one slip. A relapse is a return to old patterns. Learn the exact steps to take after a lapse to prevent it becoming a relapse.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 4, lessonNumber: 2, title: 'High-Risk Situation Planning', content: 'Identify your top 5 high-risk situations. Write a detailed response plan for each. Rehearse these mentally.', exerciseType: 'EXPOSURE' },
  { weekNumber: 4, lessonNumber: 3, title: 'If You Lapse — The Exact Steps', content: 'Step 1: Stop immediately. Step 2: Call someone. Step 3: Log it in ClearPath. Step 4: Identify the trigger. Step 5: Update your plan.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 4, lessonNumber: 4, title: 'Building a Recovery Identity', content: 'Begin defining yourself as someone who doesn\'t use. Write your new identity statement and read it daily.', exerciseType: 'REFLECTION' },
  { weekNumber: 4, lessonNumber: 5, title: 'Environmental Redesign', content: 'Remove all paraphernalia. Identify and change environmental cues that trigger use. Redesign your physical space to support your new identity.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 4, lessonNumber: 6, title: 'Accountability Systems', content: 'Establish your accountability structure: an accountability partner, daily check-in time, and a consequence for breaking commitment.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 4, lessonNumber: 7, title: 'Week 4 Reflection', content: 'How has your relationship with your high-risk situations changed? What\'s your biggest remaining vulnerability?', exerciseType: 'REFLECTION' },
  // Week 5
  { weekNumber: 5, lessonNumber: 1, title: 'Sleep and Substance Use', content: 'Explore the bidirectional relationship between substance use and sleep. Develop a sleep hygiene protocol for your recovery.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 5, lessonNumber: 2, title: 'Exercise as Craving Killer', content: 'Exercise releases dopamine naturally. Even a 10-minute walk reduces craving intensity by 30%. Build your movement prescription.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 5, lessonNumber: 3, title: 'Diet Changes During Withdrawal', content: 'Your blood sugar and hydration levels directly impact craving intensity. Learn the dietary changes that smooth withdrawal.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 5, lessonNumber: 4, title: 'Stress Management Long-Term', content: 'Build your long-term stress management system: daily practices, weekly resets, monthly reviews.', exerciseType: 'RELAXATION' },
  { weekNumber: 5, lessonNumber: 5, title: 'Social Circle Audit', content: 'Honestly evaluate which relationships support your recovery and which threaten it. Develop your boundary-setting strategy.', exerciseType: 'REFLECTION' },
  { weekNumber: 5, lessonNumber: 6, title: 'New Identity', content: '"I am someone who doesn\'t vape/smoke." Practice embodying this identity in specific situations you used to find challenging.', exerciseType: 'EXPOSURE' },
  { weekNumber: 5, lessonNumber: 7, title: 'Week 5 Reflection', content: 'How has your lifestyle changed since Week 1? What new habits have replaced the old ritual?', exerciseType: 'REFLECTION' },
  // Week 6
  { weekNumber: 6, lessonNumber: 1, title: 'Celebrating Your Progress', content: 'Review everything you\'ve accomplished. Write a letter to your Week 1 self. Acknowledge the genuine courage this journey has required.', exerciseType: 'REFLECTION' },
  { weekNumber: 6, lessonNumber: 2, title: 'Long-Term Warning Signs', content: 'Identify your personal early warning signs of relapse risk. Create a written action plan for when you notice them.', exerciseType: 'THOUGHT_RECORD' },
  { weekNumber: 6, lessonNumber: 3, title: 'Managing Anniversaries and Triggers', content: 'Plan ahead for high-risk dates: holidays, anniversaries of when you used to use heavily, stress periods.', exerciseType: 'EXPOSURE' },
  { weekNumber: 6, lessonNumber: 4, title: 'Supporting Others', content: 'Research shows that supporting others in recovery reinforces your own. Explore how you might give back to the ClearPath community.', exerciseType: 'BEHAVIORAL_ACTIVATION' },
  { weekNumber: 6, lessonNumber: 5, title: 'Building a Life You Don\'t Need to Escape From', content: 'The deepest relapse prevention is a fulfilling life. Identify and commit to 3 major life improvements that reduce the appeal of substances.', exerciseType: 'REFLECTION' },
  { weekNumber: 6, lessonNumber: 6, title: 'Your Personal Maintenance Plan', content: 'Write your comprehensive maintenance plan: daily practices, weekly check-ins, monthly reviews, annual assessments.', exerciseType: 'REFLECTION' },
  { weekNumber: 6, lessonNumber: 7, title: 'Graduation', content: 'Congratulations on completing the 6-week ClearPath CBT program. Complete your post-program self-assessment and claim your Graduation badge.', exerciseType: 'REFLECTION' },
]

cbtRouter.get('/program', async (req, res) => {
  try {
    const userId = req.user!.id
    const isFree = req.user!.subscriptionTier === 'FREE'
    const userModules = await db.select().from(cbtModules).where(eq(cbtModules.userId, userId))

    const program = CBT_CURRICULUM.map((lesson) => {
      const userModule = userModules.find(
        (m) => m.weekNumber === lesson.weekNumber && m.lessonNumber === lesson.lessonNumber
      )
      return {
        ...lesson,
        id: userModule?.id ?? null,
        completedAt: userModule?.completedAt ?? null,
        responseText: userModule?.responseText ?? null,
        aiFeedback: userModule?.aiFeedback ?? null,
        locked: isFree && lesson.weekNumber > 1,
      }
    })

    res.json({ success: true, data: program, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch CBT program' })
  }
})

cbtRouter.get('/today', async (req, res) => {
  try {
    const userId = req.user!.id
    const completed = await db.select().from(cbtModules)
      .where(and(eq(cbtModules.userId, userId)))
    const completedCount = completed.filter((m) => m.completedAt !== null).length
    const nextLesson = CBT_CURRICULUM[completedCount]
    res.json({ success: true, data: nextLesson ?? null, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch today\'s lesson' })
  }
})

cbtRouter.get('/week/:weekNum', async (req, res) => {
  try {
    const weekNum = parseInt(req.params['weekNum']!)
    const weekLessons = CBT_CURRICULUM.filter((l) => l.weekNumber === weekNum)
    const userModules = await db.select().from(cbtModules)
      .where(and(eq(cbtModules.userId, req.user!.id)))

    const lessons = weekLessons.map((lesson) => {
      const userModule = userModules.find(
        (m) => m.weekNumber === lesson.weekNumber && m.lessonNumber === lesson.lessonNumber
      )
      return { ...lesson, completedAt: userModule?.completedAt ?? null }
    })

    res.json({ success: true, data: lessons, error: null })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch week lessons' })
  }
})

cbtRouter.post('/:id/complete', async (req, res) => {
  try {
    const { responseText } = req.body as { responseText: string }
    const lessonId = req.params['id']!

    const lessonInfo = CBT_CURRICULUM.find((_, i) => String(i) === lessonId) ?? CBT_CURRICULUM[0]!

    if (req.user!.subscriptionTier === 'FREE' && lessonInfo.weekNumber > 1) {
      res.status(403).json({ success: false, data: null, error: 'Weeks 2-6 require a Premium subscription.' })
      return
    }

    const existing = await db.select().from(cbtModules)
      .where(and(
        eq(cbtModules.userId, req.user!.id),
        eq(cbtModules.weekNumber, lessonInfo.weekNumber),
        eq(cbtModules.lessonNumber, lessonInfo.lessonNumber),
      ))
      .limit(1)

    if (existing.length > 0) {
      const [updated] = await db.update(cbtModules)
        .set({ completedAt: new Date(), responseText: xss(responseText) })
        .where(eq(cbtModules.id, existing[0]!.id))
        .returning()

      // Generate AI feedback asynchronously
      generateCBTFeedback(lessonInfo.exerciseType, xss(responseText), lessonInfo.weekNumber)
        .then(async (feedback) => {
          if (feedback && existing.length > 0) {
            await db.update(cbtModules).set({ aiFeedback: feedback }).where(eq(cbtModules.id, existing[0]!.id))
          } else if (feedback && updated) {
            await db.update(cbtModules).set({ aiFeedback: feedback }).where(eq(cbtModules.id, updated.id))
          }
        })
        .catch((err) => console.error('CBT feedback generation failed:', err))

      // Queue badge evaluation
      await badgeEvaluatorQueue.add('evaluate', { userId: req.user!.id })

      res.json({ success: true, data: updated, error: null })
    } else {
      const [created] = await db.insert(cbtModules).values({
        userId: req.user!.id,
        weekNumber: lessonInfo.weekNumber,
        lessonNumber: lessonInfo.lessonNumber,
        title: lessonInfo.title,
        content: lessonInfo.content,
        exerciseType: lessonInfo.exerciseType,
        completedAt: new Date(),
        responseText: xss(responseText),
      }).returning()

      // Generate AI feedback asynchronously
      generateCBTFeedback(lessonInfo.exerciseType, xss(responseText), lessonInfo.weekNumber)
        .then(async (feedback) => {
          if (feedback && existing.length > 0) {
            await db.update(cbtModules).set({ aiFeedback: feedback }).where(eq(cbtModules.id, existing[0]!.id))
          } else if (feedback && created) {
            await db.update(cbtModules).set({ aiFeedback: feedback }).where(eq(cbtModules.id, created.id))
          }
        })
        .catch((err) => console.error('CBT feedback generation failed:', err))

      // Queue badge evaluation
      await badgeEvaluatorQueue.add('evaluate', { userId: req.user!.id })

      res.status(201).json({ success: true, data: created, error: null })
    }
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to complete lesson' })
  }
})

cbtRouter.get('/progress', async (req, res) => {
  try {
    const userModules = await db.select().from(cbtModules).where(eq(cbtModules.userId, req.user!.id))
    const completed = userModules.filter((m) => m.completedAt !== null).length
    const total = CBT_CURRICULUM.length
    res.json({
      success: true,
      data: {
        completedLessons: completed,
        totalLessons: total,
        percentComplete: Math.round((completed / total) * 100),
        currentWeek: Math.floor(completed / 7) + 1,
      },
      error: null
    })
  } catch {
    res.status(500).json({ success: false, data: null, error: 'Failed to fetch progress' })
  }
})
