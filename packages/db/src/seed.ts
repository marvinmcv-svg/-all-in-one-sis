import { neon } from '@neondatabase/serverless'
import { drizzle } from 'drizzle-orm/neon-http'
import { healthMilestones } from './schema/index.js'

async function main() {
  const sql = neon(process.env['DATABASE_URL']!)
  const db = drizzle(sql)

  const nicotineMilestones = [
    { substanceType: 'NICOTINE' as const, targetDays: 0.014, title: 'Blood Pressure Drops', description: 'Heart rate and blood pressure begin to fall', bodySystem: 'Cardiovascular', iconEmoji: '❤️', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 0.5, title: 'Carbon Monoxide Clears', description: 'CO levels in blood drop to normal', bodySystem: 'Respiratory', iconEmoji: '🫁', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 1, title: 'Nerve Endings Regrow', description: 'Sense of smell and taste begin improving', bodySystem: 'Nervous System', iconEmoji: '👃', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 3, title: 'Nicotine-Free', description: 'Nicotine fully metabolized from body; peak withdrawal', bodySystem: 'Metabolic', iconEmoji: '🎯', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 14, title: 'Circulation Improves', description: 'Blood flow throughout body significantly better', bodySystem: 'Cardiovascular', iconEmoji: '🩸', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 30, title: 'Lung Cilia Recover', description: 'Airways clear; breathing easier', bodySystem: 'Respiratory', iconEmoji: '🌬️', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 90, title: 'Dopamine Rebalance', description: 'Brain dopamine receptors largely normalized', bodySystem: 'Neurological', iconEmoji: '🧠', sourceUrl: null },
    { substanceType: 'NICOTINE' as const, targetDays: 365, title: 'Heart Disease Risk Halved', description: 'Heart attack risk drops 50%', bodySystem: 'Cardiovascular', iconEmoji: '💪', sourceUrl: null },
  ]

  const cannabisMilestones = [
    { substanceType: 'CANNABIS' as const, targetDays: 1, title: 'First Clean Day', description: 'Sleep may be disrupted — this is normal withdrawal', bodySystem: 'Neurological', iconEmoji: '🌱', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 3, title: 'Appetite Returning', description: 'Appetite changes peak and begin to resolve', bodySystem: 'Digestive', iconEmoji: '🍽️', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 7, title: 'Sleep Improving', description: 'REM sleep cycles begin restoring', bodySystem: 'Neurological', iconEmoji: '😴', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 14, title: 'Anxiety Lifting', description: 'THC-driven anxiety significantly reduced', bodySystem: 'Mental Health', iconEmoji: '😌', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 28, title: 'CB1 Receptors Reset', description: 'Cannabinoid receptors fully normalized — peak milestone', bodySystem: 'Neurological', iconEmoji: '🏆', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 60, title: 'Mental Clarity', description: 'Cognitive fog fully lifts; memory and focus sharp', bodySystem: 'Cognitive', iconEmoji: '💡', sourceUrl: null },
    { substanceType: 'CANNABIS' as const, targetDays: 90, title: 'Mood Baseline', description: 'Endocannabinoid system fully rebalanced', bodySystem: 'Mental Health', iconEmoji: '⚖️', sourceUrl: null },
  ]

  await db.insert(healthMilestones).values([...nicotineMilestones, ...cannabisMilestones])
  console.log('Health milestones seeded successfully')
  process.exit(0)
}

main().catch((err) => {
  console.error('Seed failed:', err)
  process.exit(1)
})
