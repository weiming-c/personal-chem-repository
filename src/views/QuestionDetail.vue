<template>
  <div class="question-detail-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>题目详情</h1>
      <router-link
        v-if="question"
        :to="`/questions/${question.id}/edit`"
        class="btn btn-sm btn-outline"
      >
        编辑
      </router-link>
    </div>
    <div v-if="loading" class="loading-more">加载中...</div>
    <div v-else-if="!question" class="empty-state">
      <p>题目不存在</p>
    </div>
    <div v-else class="page-body">
      <!-- 题图 -->
      <img v-if="question.imageUrl" :src="question.imageUrl" class="detail-image" />

      <!-- 题干 -->
      <div class="detail-section">
        <h3>题干</h3>
        <p class="detail-content">{{ question.content }}</p>
      </div>

      <!-- 答案 -->
      <div class="detail-section" v-if="question.answer">
        <h3>答案</h3>
        <AnswerReveal
          :answer="question.answer"
          :show-mastered="isWrongQuestion"
          @mark-wrong="handleMarkWrong"
          @mark-mastered="handleMarkMastered"
        />
      </div>

      <!-- 标签 -->
      <div class="detail-section" v-if="hasTags">
        <h3>标签</h3>
        <div class="detail-tags">
          <span v-for="t in question.systemTags" :key="'s-' + t.id" class="tag tag-system">{{ t.name }}</span>
          <span v-for="t in question.userTags" :key="'u-' + t.id" class="tag tag-user">{{ t.name }}</span>
        </div>
      </div>

      <!-- 备注 -->
      <div class="detail-section" v-if="question.remark">
        <h3>备注</h3>
        <p class="detail-content remark">{{ question.remark }}</p>
      </div>

      <!-- 来源 -->
      <div class="detail-meta">
        <span v-if="question.source === 'public'" class="tag tag-public">公共题库</span>
        <span v-else class="tag" style="background:var(--gray-100)">私有题库</span>
        <span class="detail-time">创建于 {{ formatDate(question.createdAt) }}</span>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="fixed-bottom" v-if="question">
      <button
        v-if="!isWrongQuestion"
        class="btn btn-danger btn-block"
        @click="handleMarkWrong"
      >
        加入错题本
      </button>
      <button
        v-else
        class="btn btn-success btn-block"
        @click="handleMarkMastered"
      >
        标记已掌握
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AnswerReveal from '@/components/AnswerReveal.vue'
import { useQuestionStore } from '@/stores/question'
import { useWrongQuestionStore } from '@/stores/wrongQuestion'
import { useToast } from '@/composables/useToast'
import type { Question } from '@/types'
import { getWrongQuestions, removeWrongQuestion } from '@/api'

const route = useRoute()
const questionStore = useQuestionStore()
const wrongStore = useWrongQuestionStore()
const toast = useToast()

const question = ref<Question | null>(null)
const loading = ref(true)
const isWrongQuestion = ref(false)
const wrongId = ref<number | null>(null)

const hasTags = computed(() => {
  return (question.value?.systemTags?.length || 0) + (question.value?.userTags?.length || 0) > 0
})

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function handleMarkWrong() {
  try {
    const wq = await wrongStore.mark(question.value!.id)
    isWrongQuestion.value = true
    wrongId.value = wq.id
    toast.show('已加入错题本')
  } catch {
    // Already in wrong list
    isWrongQuestion.value = true
    toast.show('已在错题本中')
  }
}

async function handleMarkMastered() {
  if (!wrongId.value) return
  try {
    await wrongStore.update(wrongId.value, { status: 'mastered' })
    isWrongQuestion.value = false
    toast.show('已标记为掌握')
  } catch {
    toast.show('操作失败')
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    question.value = await questionStore.fetchQuestion(id)
  } catch {
    // not found
  } finally {
    loading.value = false
  }

  // Check if in wrong list
  try {
    const wr = await getWrongQuestions({ page: 1, pageSize: 1 })
    const found = wr.items.find((w: any) => w.questionId === id)
    if (found && found.status === 'active') {
      isWrongQuestion.value = true
      wrongId.value = found.id
    }
  } catch {
    // ignore
  }
})
</script>

<style scoped>
.detail-image {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: var(--radius);
  margin-bottom: 20px;
  background: var(--gray-100);
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-500);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-content {
  font-size: 16px;
  line-height: 1.8;
  color: var(--gray-800);
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-content.remark {
  font-size: 14px;
  color: var(--gray-600);
  background: var(--gray-50);
  padding: 12px;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--gray-300);
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-100);
}

.detail-time {
  font-size: 12px;
  color: var(--gray-400);
}
</style>
