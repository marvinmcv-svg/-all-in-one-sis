// Service worker: daily reminder alarm + blocked sites enforcement

const PEAK_CRAVING_HOUR = 20 // 8 PM default, overridden by prediction data

chrome.runtime.onInstalled.addListener(() => {
  // Schedule daily craving reminder
  chrome.alarms.create('daily-reminder', {
    when: getNextAlarmTime(PEAK_CRAVING_HOUR),
    periodInMinutes: 24 * 60,
  })
})

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'daily-reminder') {
    chrome.notifications.create('craving-reminder', {
      type: 'basic',
      iconUrl: 'icon32.png',
      title: 'ClearPath Check-in',
      message: "How are you feeling? Log a craving or journal entry to stay on track.",
      priority: 1,
    })
  }
})

chrome.notifications.onClicked.addListener((notificationId) => {
  if (notificationId === 'craving-reminder') {
    chrome.action.openPopup?.()
    chrome.notifications.clear(notificationId)
  }
})

// Update blocked sites from storage
chrome.storage.onChanged.addListener((changes) => {
  if (changes['blocked_urls']) {
    updateBlockedSites(changes['blocked_urls'].newValue as string[])
  }
})

async function updateBlockedSites(urls: string[]): Promise<void> {
  const existingRules = await chrome.declarativeNetRequest.getDynamicRules()
  const removeIds = existingRules.map((r) => r.id)

  const addRules = urls.map((url, i) => ({
    id: i + 1,
    priority: 1,
    action: {
      type: chrome.declarativeNetRequest.RuleActionType.REDIRECT,
      redirect: { extensionPath: '/blocked.html' },
    } as chrome.declarativeNetRequest.RuleAction,
    condition: {
      urlFilter: url,
      resourceTypes: [chrome.declarativeNetRequest.ResourceType.MAIN_FRAME],
    },
  }))

  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: removeIds, addRules })
}

function getNextAlarmTime(hour: number): number {
  const now = new Date()
  const target = new Date()
  target.setHours(hour, 0, 0, 0)
  if (target <= now) target.setDate(target.getDate() + 1)
  return target.getTime()
}
