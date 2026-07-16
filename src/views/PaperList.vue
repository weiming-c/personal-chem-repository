<template>
  <div class="paper-list-page">
    <div class="page-header">
      <h1>试卷列表</h1>
      <router-link to="/papers/new" class="btn btn-sm btn-primary">组卷</router-link>
    </div>
    <div class="page-body">
      <div v-if="loading && papers.length === 0" class="loading-more">加载中...</div>
      <div v-else-if="papers.length === 0" class="empty-state">
        <div class="icon">📄</div>
        <p>暂无试卷，去组一张吧</p>
      </div>
      <div v-else>
        <div v-for="p in papers" :key="p.id" class="paper-card card">
          <div class="paper-info" @click="$router.push(`/papers/${p.id}/practice`)">
            <h3>{{ p.name }}</h3>
            <p v-if="p.description" class="paper-desc">{{ p.description }}</p>
            <div class="paper-meta">
              <span>{{ p.questionIds?.length || 0 }} 题</span>
              <span class="paper-source">
                {{ sourceLabel(p.sourceMode) }}
              </span>
              <span class="paper-date">{{ formatDate(p.createdAt) }}</span>
            </div>
          </div>
          <div class="paper-actions">
            <button class="btn btn-sm btn-primary" @click="$router.push(`/papers/${p.id}/practice`)">
              开始练习
            </button>
            <button class="btn btn-sm btn-ghost" @click="handleDelete(p)">删除</button>
          </div>
        </div>
        <div v-if="hasMore" class="loading-more" @click="loadMore">{{ loading ? '加载中...' : '加载更多' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePaperStore } from '@/stores/paper'
import { useToast } from '@/composables/useToast'
import type { Paper } from '@/types'

const paperStore = usePaperStore()
const toast = useToast()

const papers = ref<Paper[]>([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(false)
const pageSize = 20

function sourceLabel(mode: string) {
  return { private: '私有', public: '公共', mixed: '混合' }[mode] || mode
}

function formatDate(d: string) {
  if (!d) return ''
  const dt = new Date(d)
  return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`
}

async function loadPapers() {
  loading.value = true; page.value = 1
  try {
    await paperStore.fetchPapers({ page: 1, pageSize })
    papers.value = paperStore.papers
    hasMore.value = paperStore.papers.length < paperStore.total
  } finally { loading.value = false }
}

async function loadMore() {
  if (loading.value || !hasMore.value) return
  loading.value = true; page.value++
  try {
    await paperStore.fetchPapers({ page: page.value, pageSize })
    papers.value = paperStore.papers
    hasMore.value = paperStore.papers.length < paperStore.total
  } finally { loading.value = false }
}

async function handleDelete(p: Paper) {
  if (!confirm('确认删除该试卷？')) return
  try {
    await paperStore.removePaper(p.id)
    papers.value = papers.value.filter(x => x.id !== p.id)
    toast.show('已删除')
  } catch { toast.show('删除失败') }
}

onMounted(loadPapers)
</script>

<style scoped>
.paper-card { cursor: pointer; }
.paper-info h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.paper-desc { font-size: 13px; color: var(--gray-500); margin-bottom: 8px; }
.paper-meta { display: flex; gap: 12px; font-size: 12px; color: var(--gray-400); }
.paper-source { color: var(--primary); }
.paper-date { margin-left: auto; }
.paper-actions { display: flex; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--gray-100); }
</style>
