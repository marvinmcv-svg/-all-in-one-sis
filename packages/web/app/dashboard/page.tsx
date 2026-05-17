import { auth } from '@clerk/nextjs/server'
import { StatsCard } from '@/components/dashboard/StatsCard'
import { HealthTimeline } from '@/components/dashboard/HealthTimeline'
import { WeeklyChart } from '@/components/dashboard/WeeklyChart'
import { BadgeReel } from '@/components/dashboard/BadgeReel'
import { QuickLogModal } from '@/components/dashboard/QuickLogModal'

export default async function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <QuickLogModal />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard type="days" />
        <StatsCard type="streak" />
        <StatsCard type="money" />
        <StatsCard type="cravings" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <WeeklyChart />
        <HealthTimeline />
      </div>

      <BadgeReel />
    </div>
  )
}
