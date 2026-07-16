import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Paper, CreatePaperData } from '@/types'
import { createPaper, getPapers, getPaper, deletePaper } from '@/api'

export const usePaperStore = defineStore('paper', () => {
  const papers = ref<Paper[]>([])
  const currentPaper = ref<Paper | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchPapers(params?: { page?: number; pageSize?: number }) {
    loading.value = true
    try {
      const res = await getPapers(params)
      papers.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchPaper(id: number) {
    currentPaper.value = await getPaper(id)
    return currentPaper.value
  }

  async function addPaper(data: CreatePaperData) {
    return await createPaper(data)
  }

  async function removePaper(id: number) {
    await deletePaper(id)
    papers.value = papers.value.filter((p) => p.id !== id)
  }

  return {
    papers,
    currentPaper,
    total,
    loading,
    fetchPapers,
    fetchPaper,
    addPaper,
    removePaper,
  }
})
