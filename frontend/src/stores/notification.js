import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMyNotifications } from '@/api/notification'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)

  async function fetchUnreadCount() {
    try {
      const res = await getMyNotifications({ page: 1, page_size: 100 })
      if (res.code === 0) {
        unreadCount.value = res.data.filter(n => n.read_status === 0).length
      }
    } catch (error) {
      console.error('Failed to fetch unread count:', error)
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
  }
})
