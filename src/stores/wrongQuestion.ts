import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WrongQuestion, WrongQuestionFilterParams, UpdateWrongQuestionData, Paper } from '@/types'
import { getWrongQuestions, markWrongQuestion, updateWrongQuestion, removeWrongQuestion } from '@/api'

export const useWrongQuestionStore = defineStore('wrongQuestion', () => {
  const wrongQuestions = ref<WrongQuestion[]>([])
  const total = ref(0)
  const loading = ref(false)

  async function fetchWrongQuestions(params: WrongQuestionFilterParams) {
    loading.value = true
    try {
      const res = await getWrongQuestions(params)
      wrongQuestions.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function mark(questionId: number) {
    return await markWrongQuestion(questionId)
  }

  async function update(id: number, data: UpdateWrongQuestionData) {
    const updated = await updateWrongQuestion(id, data)
    const idx = wrongQuestions.value.findIndex((w) => w.id === id)
    if (idx !== -1) {
      wrongQuestions.value[idx] = updated
    }
    return updated
  }

  async function remove(id: number) {
    await removeWrongQuestion(id)
    wrongQuestions.value = wrongQuestions.value.filter((w) => w.id !== id)
  }

  return {
    wrongQuestions,
    total,
    loading,
    fetchWrongQuestions,
    mark,
    update,
    remove,
  }
})
