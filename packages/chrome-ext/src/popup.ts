// Popup controller: craving log form + mini stats dashboard

interface Stats {
  daysClean: number
  moneySavedCents: number
  lastBadge?: { iconEmoji: string; title: string }
}

const API_BASE = 'https://api.clearpath.app'

async function getStoredToken(): Promise<string | null> {
  return new Promise((resolve) => {
    chrome.storage.local.get(['auth_token'], (result) => {
      resolve((result['auth_token'] as string | undefined) ?? null)
    })
  })
}

async function fetchStats(token: string): Promise<Stats | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/stats`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await res.json() as { success: boolean; data: { daysClean: number; moneySavedCents: number } }
    if (!data.success) return null
    return { daysClean: data.data.daysClean, moneySavedCents: data.data.moneySavedCents }
  } catch {
    return null
  }
}

async function logCraving(token: string, intensity: string, triggered: boolean): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cravings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ substanceType: 'NICOTINE', intensity, triggered, triggerTags: [], mood: 5 }),
    })
    return res.ok
  } catch {
    return false
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const token = await getStoredToken()

  const statsEl = document.getElementById('stats')
  const formEl = document.getElementById('form')
  const loginEl = document.getElementById('login')

  if (!token) {
    loginEl?.classList.remove('hidden')
    statsEl?.classList.add('hidden')
    formEl?.classList.add('hidden')
    return
  }

  // Load stats
  const stats = await fetchStats(token)
  if (stats && statsEl) {
    statsEl.innerHTML = `
      <div class="stat"><span class="num">${stats.daysClean}</span><span class="label">days clean</span></div>
      <div class="stat"><span class="num">$${(stats.moneySavedCents / 100).toFixed(0)}</span><span class="label">saved</span></div>
    `
  }

  // Log craving
  document.getElementById('beat-it')?.addEventListener('click', async () => {
    const intensity = (document.getElementById('intensity') as HTMLSelectElement)?.value ?? 'MEDIUM'
    const ok = await logCraving(token, intensity, false)
    if (ok) {
      document.getElementById('success')?.classList.remove('hidden')
      formEl?.classList.add('hidden')
    }
  })

  document.getElementById('used')?.addEventListener('click', async () => {
    const intensity = (document.getElementById('intensity') as HTMLSelectElement)?.value ?? 'MEDIUM'
    await logCraving(token, intensity, true)
    document.getElementById('success')?.classList.remove('hidden')
    formEl?.classList.add('hidden')
  })
})
