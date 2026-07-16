<template>
  <div class="question-list-page">
    <div class="page-header">
      <h1>题库</h1>
      <router-link to="/questions/new" class="btn btn-sm btn-primary">录入</router-link>
    </div>
    <div class="page-body">
      <!-- 筛选条 -->
      <div class="filter-bar">
        <select v-model="filterTagId" class="form-input" style="width:auto;flex:1" @change="loadQuestions">
          <option :value="0">全部标签</option>
          <optgroup v-for="n in tagStore.systemTags" :key="n.id" :label="n.name">
            <option v-if="n.children" v-for="c in n.children" :key="c.id" :value="c.id">{{ c.name }}</option>
            <option :value="n.id">📁 {{ n.name }}</option>
          </optgroup>
        </select>
        <select v-model="filterSource" class="form-input" style="width:auto" @change="loadQuestions">
          <option value="">全部来源</option>
          <option value="private">私有</option>
          <option value="public">公共</option>
        </select>
      </div>

      <!-- 列表 -->
      <div v-if="loading && questions.length === 0" class="loading-more">加载中...</div>
      <div v-else-if="questions.length === 0" class="empty-state">
        <div class="icon">📚</div>
        <p>暂无题目</p>
      </div>
      <div v-else>
        <QuestionCard
          v-for="q in questions"
          :key="q.id"
          :question="q"
          @click="$router.push(`/questions/${q.id}`)"
        />
        <!-- 加载更多 -->
        <div v-if="hasMore" class="loading-more" @click="loadMore">
          {{ loading ? '加载中...' : '加载更多' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import QuestionCard from '@/components/QuestionCard.vue'
import { getQuestions } from '@/api'
import type { Question } from '@/types'
import { useTagStore } from '@/stores/tag'

const tagStore = useTagStore()
const questions = ref<Question[]>([])
const loading = ref(false)
const filterTagId = ref(0)
const filterSource = ref('')
const page = ref(1)
const total = ref(0)
const pageSize = 20

const hasMore = ref(false)

async function loadQuestions() {
  loading.value = true
  page.value = 1
  try {
    const params: any = { page: 1, pageSize }
    if (filterTagId.value > 0) {
      params.system_tag_id = filterTagId.value
    }
    if (filterSource.value) {
      params.source = filterSource.value
    }
    const res = await getQuestions(params)
    questions.value = res.items
    total.value = res.total
    hasMore.value = res.items.length < res.total
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || !hasMore.value) return
  loading.value = true
  page.value++
  try {
    const params: any = { page: page.value, pageSize }
    if (filterTagId.value > 0) {
      params.system_tag_id = filterTagId.value
    }
    if (filterSource.value) {
      params.source = filterSource.value
    }
    const res = await getQuestions(params)
    questions.value.push(...res.items)
    hasMore.value = questions.value.length < res.total
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await tagStore.fetchSystemTags()
  } catch {
    // 标签服务暂未就绪，不影响题目列表加载
  }
  await loadQuestions()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-bar select {
  font-size: 14px;
  padding: 8px 12px;
}
</style>
