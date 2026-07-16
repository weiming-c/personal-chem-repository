import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Question, CreateQuestionData, UpdateQuestionData, PaginationParams } from '@/types'
import { createQuestion, getQuestions, getQuestion, updateQuestion, deleteQuestion } from '@/api'

export const useQuestionStore = defineStore('question', () => {
  const questions = ref<Question[]>([])
  const currentQuestion = ref<Question | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function fetchQuestions(params: PaginationParams & Record<string, any>) {
    loading.value = true
    try {
      const res = await getQuestions(params)
      questions.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchQuestion(id: number) {
    currentQuestion.value = await getQuestion(id)
    return currentQuestion.value
  }

  async function addQuestion(data: CreateQuestionData) {
    return await createQuestion(data)
  }

  async function editQuestion(id: number, data: UpdateQuestionData) {
    const updated = await updateQuestion(id, data)
    if (currentQuestion.value?.id === id) {
      currentQuestion.value = updated
    }
    return updated
  }

  async function removeQuestion(id: number) {
    await deleteQuestion(id)
    questions.value = questions.value.filter((q) => q.id !== id)
  }

  return {
    questions,
    currentQuestion,
    total,
    loading,
    fetchQuestions,
    fetchQuestion,
    addQuestion,
    editQuestion,
    removeQuestion,
  }
})
