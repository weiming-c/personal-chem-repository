z<template>
  <div class="home-page">
    <div class="page-header">
      <h1>化学竞赛题库</h1>
    </div>
    <div class="page-body">
      <!-- 快捷操作区 -->
      <div class="quick-actions">
        <div class="action-card" @click="$router.push('/questions/new')">
          <span class="action-icon">➕</span>
          <span class="action-label">录入新题</span>
        </div>
        <div class="action-card" @click="$router.push('/search')">
          <span class="action-icon">🔍</span>
          <span class="action-label">检索题目</span>
        </div>
        <div class="action-card" @click="$router.push('/wrong-questions')">
          <span class="action-icon">📝</span>
          <span class="action-label">错题本</span>
        </div>
        <div class="action-card" @click="$router.push('/papers/new')">
          <span class="action-icon">📋</span>
          <span class="action-label">智能组卷</span>
        </div>
        <div class="action-card" @click="$router.push('/tags')">
          <span class="action-icon">🏷️</span>
          <span class="action-label">标签管理</span>
        </div>
      </div>

      <!-- 最近题目 -->
      <div class="section">
        <div class="section-header">
          <h2>最近录入</h2>
          <router-link to="/questions" class="section-link">全部</router-link>
        </div>
        <div v-if="loading" class="loading-more">加载中...</div>
        <div v-else-if="recentQuestions.length === 0" class="empty-state">
          <div class="icon">📚</div>
          <p>还没有题目，去录入第一道题吧</p>
        </div>
        <QuestionCard
          v-for="q in recentQuestions"
          :key="q.id"
          :question="q"
          @click="$router.push(`/questions/${q.id}`)"
        />
      </div>

      <!-- 待复习错题 -->
      <div class="section" v-if="wrongToReview > 0">
        <div class="section-header">
          <h2>待复习错题</h2>
          <router-link to="/wrong-questions" class="section-link">
            {{ wrongToReview }} 道待复习
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import QuestionCard from '@/components/QuestionCard.vue'
import { useQuestionStore } from '@/stores/question'
import { getWrongQuestions } from '@/api'

const questionStore = useQuestionStore()
const recentQuestions = ref<any[]>([])
const loading = ref(true)
const wrongToReview = ref(0)

onMounted(async () => {
  try {
    const res = await import('@/api').then((m) =>
      m.getQuestions({ page: 1, pageSize: 6 })
    )
    recentQuestions.value = res.items
  } catch {
    // ignore
  } finally {
    loading.value = false
  }

  try {
    const wr = await getWrongQuestions({ page: 1, pageSize: 1, status: 'active' as any })
    wrongToReview.value = wr.total
  } catch {
    // ignore
  }
})
</script>

<style scoped>
.home-page {
  padding-bottom: 80px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 12px;
  background: #fff;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: all .15s;
}

.action-card:active {
  transform: scale(.95);
  box-shadow: var(--shadow-md);
}

.action-icon {
  font-size: 28px;
}

.action-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--gray-700);
}

.section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header h2 {
  font-size: 17px;
  font-weight: 600;
}

.section-link {
  font-size: 13px;
}
</style>
