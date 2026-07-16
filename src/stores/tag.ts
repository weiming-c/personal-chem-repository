import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SystemTag, UserTag } from '@/types'
import { getSystemTags, getUserTags, createUserTag, deleteUserTag } from '@/api'

export const useTagStore = defineStore('tag', () => {
  const systemTags = ref<SystemTag[]>([])
  const userTags = ref<UserTag[]>([])
  const systemTagsLoaded = ref(false)
  const userTagsLoaded = ref(false)

  async function fetchSystemTags() {
    if (systemTagsLoaded.value) return
    systemTags.value = await getSystemTags()
    systemTagsLoaded.value = true
  }

  async function fetchUserTags() {
    userTags.value = await getUserTags()
    userTagsLoaded.value = true
  }

  async function addUserTag(name: string) {
    const tag = await createUserTag(name)
    userTags.value.push(tag)
    return tag
  }

  async function removeUserTag(id: number) {
    await deleteUserTag(id)
    userTags.value = userTags.value.filter((t) => t.id !== id)
  }

  return {
    systemTags,
    userTags,
    systemTagsLoaded,
    userTagsLoaded,
    fetchSystemTags,
    fetchUserTags,
    addUserTag,
    removeUserTag,
  }
})
