import { UserButton } from '@clerk/nextjs'

export function TopBar() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="text-sm text-gray-500">
        {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
      </div>
      <UserButton afterSignOutUrl="/" />
    </header>
  )
}
