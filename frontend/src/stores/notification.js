import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUnreadCount } from '@/api/notification'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  let pollTimer = null

  async function fetchUnreadCount() {
    try {
      const res = await getUnreadCount()
      if (res.code === 0) {
        unreadCount.value = res.data.count
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
    }
  }

  function startPolling(intervalMs = 30000) {
    // Poll every 30 seconds
    if (pollTimer) return
    fetchUnreadCount()
    pollTimer = setInterval(fetchUnreadCount, intervalMs)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function decrementUnread() {
    if (unreadCount.value > 0) {
      unreadCount.value--
    }
  }

  return {
    unreadCount,
    fetchUnreadCount,
    decrementUnread,
    startPolling,
    stopPolling,
  }
})
