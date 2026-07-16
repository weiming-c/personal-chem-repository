<template>
  <div class="practice-page">
    <!-- 顶部导航 -->
    <div class="practice-header">
      <button class="back-btn" @click="handleExit">←</button>
      <span class="progress-text">{{ currentIndex + 1 }} / {{ questions.length }}</span>
      <button class="btn btn-sm btn-ghost" @click="toggleMode">
        {{ showAllAnswers ? '逐个查看' : '答案全览' }}
      </button>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
    </div>

    <div class="page-body" v-if="questions.length > 0">
      <!-- 题目 -->
      <div class="question-card practice-card">
        <img v-if="currentQuestion.imageUrl" :src="currentQuestion.imageUrl" class="question-img" />
        <div class="question-number">第 {{ currentIndex + 1 }} 题</div>
        <!-- 标签 -->
        <div class="question-tags" v-if="hasTags">
          <span v-for="t in currentQuestion.systemTags || []" :key="'s-'+t.id" class="tag tag-system">{{ t.name }}</span>
          <span v-for="t in currentQuestion.userTags || []" :key="'u-'+t.id" class="tag tag-user">{{ t.name }}</span>
        </div>
      </div>

      <!-- 答案区域 -->
      <div v-if="showAllAnswers || answerRevealed" class="answer-section">
        <h3>答案</h3>
        <img v-if="currentQuestion.answerImageUrl" :src="currentQuestion.answerImageUrl" class="answer-img" />
        <div class="answer-actions">
          <button class="btn btn-sm btn-danger" @click="handleMarkWrong">
            📝 加入错题本
          </button>
          <button class="btn btn-sm btn-success" @click="handleMarkMastered">
            ✅ 已掌握
          </button>
        </div>
      </div>
      <div v-else class="answer-reveal-btn" @click="revealAnswer">
        <span>🔒</span> 点击查看答案
      </div>

      <!-- 导航按钮 -->
      <div class="nav-buttons">
        <button class="btn btn-outline" :disabled="currentIndex === 0" @click="prevQuestion">上一题</button>
        <span class="nav-hint"></span>
        <button v-if="currentIndex < questions.length - 1" class="btn btn-primary" @click="nextQuestion">下一题</button>
        <button v-else class="btn btn-success" @click="handleFinish">完成</button>
      </div>
    </div>

    <div v-else class="empty-state" style="padding-top:100px">
      <div class="icon">📄</div>
      <p>试卷为空</p>
      <button class="btn btn-outline" @click="$router.back()">返回</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaperStore } from '@/stores/paper'
import { useWrongQuestionStore } from '@/stores/wrongQuestion'
import { useToast } from '@/composables/useToast'
import type { Question } from '@/types'
import { getQuestion } from '@/api'

const route = useRoute()
const router = useRouter()
const paperStore = usePaperStore()
const wrongStore = useWrongQuestionStore()
const toast = useToast()

const currentIndex = ref(0)
const answerRevealed = ref(false)
const showAllAnswers = ref(false)
const questions = ref<Question[]>([])
const masteredSet = ref(new Set<number>())
const wrongSet = ref(new Set<number>())

const currentQuestion = computed(() => questions.value[currentIndex.value] || ({} as Question))
const hasTags = computed(() => (currentQuestion.value.systemTags?.length || 0) + (currentQuestion.value.userTags?.length || 0) > 0)
const progressPct = computed(() => questions.value.length > 0 ? ((currentIndex.value + 1) / questions.value.length) * 100 : 0)

function revealAnswer() {
  answerRevealed.value = true
}

function toggleMode() {
  showAllAnswers.value = !showAllAnswers.value
  if (showAllAnswers.value) answerRevealed.value = true
}

function prevQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    answerRevealed.value = showAllAnswers.value
  }
}

function nextQuestion() {
  if (currentIndex.value < questions.value.length - 1) {
    currentIndex.value++
    answerRevealed.value = showAllAnswers.value
  }
}

async function handleMarkWrong() {
  const q = currentQuestion.value
  if (wrongSet.value.has(q.id)) return
  try {
    await wrongStore.mark(q.id)
    wrongSet.value.add(q.id)
    toast.show('已加入错题本')
  } catch { toast.show('可能在错题本中') }
}

async function handleMarkMastered() {
  const q = currentQuestion.value
  masteredSet.value.add(q.id)
  toast.show('已标记')
  // auto advance
  if (currentIndex.value < questions.value.length - 1) {
    setTimeout(() => nextQuestion(), 400)
  }
}

function handleExit() {
  if (masteredSet.value.size > 0 || wrongSet.value.size > 0) {
    router.back()
  } else {
    router.back()
  }
}

function handleFinish() {
  const msg = masteredSet.value.size > 0
    ? `掌握 ${masteredSet.value.size} 题`
    : '练习结束'
  toast.show(msg)
  setTimeout(() => router.back(), 1500)
}

onMounted(async () => {
  const paperId = Number(route.params.id)
  try {
    const paper = await paperStore.fetchPaper(paperId)
    const ids = paper.questionIds || []
    if (ids.length > 0) {
      // Fetch questions one by one in parallel
      const qs = await Promise.all(
        ids.map(id => getQuestion(id).catch(() => null))
      )
      questions.value = qs.filter(Boolean) as Question[]
    }
  } catch {
    toast.show('加载试卷失败')
  }
})
</script>

<style scoped>
.practice-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-bottom: 1px solid var(--gray-100);
  position: sticky;
  top: 0;
  z-index: 10;
  gap: 8px;
}

.progress-text {
  flex: 1;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-600);
}

.progress-bar {
  height: 3px;
  background: var(--gray-100);
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width .3s;
}

.practice-card {
  padding: 20px;
  margin-bottom: 16px;
}

.question-img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
  background: var(--gray-100);
}

.question-number {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 12px;
}

.question-tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.answer-section {
  margin-bottom: 16px;
  padding: 16px;
  border: 1.5px solid var(--success);
  border-radius: var(--radius);
  background: var(--success-bg);
}

.answer-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--success);
  margin-bottom: 8px;
}

.answer-img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  background: #fff;
}

.answer-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(5, 150, 105, .15);
}

.answer-reveal-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  border: 1.5px dashed var(--gray-300);
  border-radius: var(--radius);
  cursor: pointer;
  color: var(--gray-500);
  font-size: 15px;
  margin-bottom: 16px;
  transition: all .2s;
}

.answer-reveal-btn:active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.nav-buttons {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 20px;
}

.nav-hint { flex: 1; }
</style>
