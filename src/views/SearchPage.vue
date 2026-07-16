<template>
  <div class="search-page">
    <div class="page-header">
      <h1>检索题目</h1>
    </div>
    <div style="padding-top:12px">
      <SearchBar
        ref="searchBarRef"
        v-model="searchKeyword"
        @search="handleSearch"
        @ai-search="handleAiSearch"
      />
    </div>

    <!-- 标签筛选 -->
    <div class="tag-filter-bar" v-if="selectedSystemTags.length > 0">
      <span class="filter-label">系统标签：</span>
      <span
        v-for="t in selectedSystemTags"
        :key="t.id"
        class="tag tag-system"
        style="cursor:pointer"
        @click="removeSystemTag(t)"
      >
        {{ t.name }} ×
      </span>
    </div>

    <div class="page-body">
      <!-- AI 智能搜索提示 -->
      <div v-if="aiSuggest" class="ai-suggestion">
        <span class="ai-icon">✨</span>
        <span>AI 建议搜索：{{ aiSuggest }}</span>
      </div>

      <!-- 结果 -->
      <div v-if="loading && results.length === 0" class="loading-more">搜索中...</div>
      <div v-else-if="searched && results.length === 0" class="empty-state">
        <div class="icon">🔍</div>
        <p>未找到匹配的题目</p>
        <p class="form-hint">试试 AI 智能搜索或其他关键词</p>
      </div>
      <div v-else-if="results.length > 0">
        <p class="result-count">找到 {{ total }} 条结果</p>
        <QuestionCard
          v-for="q in results"
          :key="q.id"
          :question="q"
          @click="$router.push(`/questions/${q.id}`)"
        />
        <div v-if="hasMore" class="loading-more" @click="loadMore">
          {{ loading ? '加载中...' : '加载更多' }}
        </div>
      </div>
    </div>

    <!-- 系统标签选择弹窗 -->
    <teleport to="body">
      <div v-if="showTagModal" class="modal-overlay" @click.self="showTagModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <span>筛选系统标签</span>
            <button class="btn btn-sm btn-ghost" @click="showTagModal = false">关闭</button>
          </div>
          <div class="modal-body">
            <TagTree
              :nodes="tagStore.systemTags"
              :selectedIds="filterSystemTagIds"
              :expandedIds="expandedIds"
              @toggle-select="handleTagToggle"
              @toggle-expand="handleExpand"
            />
          </div>
        </div>
      </div>
    </teleport>

    <!-- 浮动标签筛选按钮 -->
    <button class="fab-tag" @click="showTagModal = true" v-show="results.length > 0 || searched">
      <span>🏷️</span>
      <span v-if="filterSystemTagIds.length > 0" class="fab-badge">{{ filterSystemTagIds.length }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SearchBar from '@/components/SearchBar.vue'
import QuestionCard from '@/components/QuestionCard.vue'
import TagTree from '@/components/TagTree.vue'
import { searchQuestions, aiTranslate } from '@/api'
import { useTagStore } from '@/stores/tag'
import { useToast } from '@/composables/useToast'
import type { Question, SystemTag, AiTranslateResult } from '@/types'

const tagStore = useTagStore()
const toast = useToast()

const searchBarRef = ref()
const searchKeyword = ref('')
const filterSystemTagIds = ref<number[]>([])
const results = ref<Question[]>([])
const total = ref(0)
const loading = ref(false)
const searched = ref(false)
const page = ref(1)
const hasMore = ref(false)
const pageSize = 20
const searchScope = ref<'content' | 'content_answer'>('content_answer')
const searchRange = ref<'private' | 'all'>('all')
const aiSuggest = ref('')
const showTagModal = ref(false)
const expandedIds = ref(new Set<number>())
const lastSearchParams = ref<any>(null)

const selectedSystemTags = computed(() => {
  return findSystemTags(tagStore.systemTags, filterSystemTagIds.value)
})

function findSystemTags(nodes: SystemTag[], ids: number[]): SystemTag[] {
  let result: SystemTag[] = []
  for (const node of nodes) {
    if (ids.includes(node.id)) result.push(node)
    if (node.children) result = result.concat(findSystemTags(node.children, ids))
  }
  return result.slice(0, 5)
}

async function handleSearch(params: { keyword: string; searchScope: string; searchRange: string }) {
  if (!params.keyword.trim() && filterSystemTagIds.value.length === 0) {
    toast.show('请输入搜索关键词或选择标签')
    return
  }
  searchScope.value = params.searchScope as any
  searchRange.value = params.searchRange as any
  page.value = 1
  loading.value = true
  searched.value = true
  aiSuggest.value = ''

  lastSearchParams.value = {
    keyword: params.keyword,
    searchScope: searchScope.value,
    searchRange: searchRange.value,
    systemTagIds: filterSystemTagIds.value.length > 0 ? [...filterSystemTagIds.value] : undefined,
  }

  try {
    const res = await searchQuestions({
      ...lastSearchParams.value,
      page: 1,
      pageSize,
    })
    results.value = res.items
    total.value = res.total
    hasMore.value = res.items.length < res.total
  } catch {
    toast.show('搜索失败')
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || !hasMore.value || !lastSearchParams.value) return
  loading.value = true
  page.value++
  try {
    const res = await searchQuestions({
      ...lastSearchParams.value,
      page: page.value,
      pageSize,
    })
    results.value.push(...res.items)
    hasMore.value = results.value.length < res.total
  } finally {
    loading.value = false
  }
}

async function handleAiSearch() {
  if (!searchKeyword.value.trim()) {
    toast.show('请输入搜索关键词')
    return
  }
  toast.show('AI 思考中...')
  try {
    const result = await aiTranslate(searchKeyword.value)
    aiSuggest.value = result.translatedKeywords
    searchKeyword.value = result.translatedKeywords
    handleSearch({
      keyword: result.translatedKeywords,
      searchScope: searchScope.value,
      searchRange: searchRange.value,
    })
  } catch {
    toast.show('AI 搜索暂不可用，使用原词搜索')
    handleSearch({
      keyword: searchKeyword.value,
      searchScope: searchScope.value,
      searchRange: searchRange.value,
    })
  }
}

function handleTagToggle(node: SystemTag) {
  const idx = filterSystemTagIds.value.indexOf(node.id)
  if (idx === -1) {
    filterSystemTagIds.value.push(node.id)
  } else {
    filterSystemTagIds.value.splice(idx, 1)
  }
}

function handleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

function removeSystemTag(tag: SystemTag) {
  filterSystemTagIds.value = filterSystemTagIds.value.filter((id) => id !== tag.id)
}

onMounted(async () => {
  await tagStore.fetchSystemTags()
})
</script>

<style scoped>
.tag-filter-bar {
  padding: 0 20px;
  margin-top: 10px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.filter-label {
  font-size: 12px;
  color: var(--gray-500);
  margin-right: 4px;
}

.ai-suggestion {
  margin-bottom: 16px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #faf5ff, #ede9fe);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--primary-dark);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 18px;
}

.result-count {
  font-size: 13px;
  color: var(--gray-500);
  margin-bottom: 10px;
}

.fab-tag {
  position: fixed;
  bottom: 80px;
  right: 20px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  border: none;
  font-size: 20px;
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fab-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
