<template>
  <div class="search-page">
    <div class="browse-header">
      <h1>检索题目</h1>
      <button class="btn btn-sm btn-ghost filter-toggle" @click="sidebarOpen = !sidebarOpen">
        🏷️ 标签
        <span v-if="filterSystemTagIds.length > 0" class="filter-count">{{ filterSystemTagIds.length }}</span>
      </button>
    </div>

    <div class="search-row">
      <SearchBar
        ref="searchBarRef"
        v-model="searchKeyword"
        @search="handleSearch"
        @ai-search="handleAiSearch"
      />
    </div>

    <!-- AI 建议 -->
    <div v-if="aiSuggest" class="ai-suggestion">
      <span class="ai-icon">✨</span>
      <span>AI 建议搜索：{{ aiSuggest }}</span>
    </div>

    <!-- 已选筛选标签 -->
    <div v-if="selectedSystemTags.length > 0" class="active-filters">
      <span class="filter-hint">筛选：</span>
      <span
        v-for="t in selectedSystemTags"
        :key="t.id"
        class="filter-chip filter-chip--system"
        @click="removeSystemTag(t)"
      >
        {{ t.name }} <span class="chip-x">×</span>
      </span>
      <button class="btn btn-sm btn-ghost filter-clear" @click="clearAllTags">清除</button>
    </div>

    <!-- 主体：侧边栏 + 结果 -->
    <div class="browse-body">
      <!-- 遮罩 -->
      <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

      <!-- 侧边栏 -->
      <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
        <div class="sidebar-header">
          <span class="sidebar-title">标签筛选</span>
          <button class="btn btn-sm btn-ghost" @click="sidebarOpen = false">✕</button>
        </div>

        <div class="sidebar-section">
          <h3 class="sidebar-section-title">🏷️ 系统标签</h3>
          <div v-if="!tagStore.systemTagsLoaded" class="sidebar-loading">加载中...</div>
          <div v-else class="tag-category-list">
            <div
              v-for="cat in tagStore.systemTags"
              :key="cat.id"
              class="tag-category"
            >
              <div class="category-header" @click="toggleExpand(cat.id)">
                <span class="category-arrow" :class="{ expanded: expandedIds.has(cat.id) }">▶</span>
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">{{ countSelectedIn(cat) }}</span>
              </div>
              <div v-if="cat.children && expandedIds.has(cat.id)" class="category-children">
                <button class="tag-quick-btn" @click="selectAllInCat(cat, true)">全选</button>
                <button class="tag-quick-btn tag-quick-btn--clear" @click="selectAllInCat(cat, false)">清除</button>
                <div
                  v-for="child in cat.children"
                  :key="child.id"
                  class="tag-chip"
                  :class="{ 'tag-chip--active': filterSystemTagIds.includes(child.id) }"
                  @click="handleTagToggle(child)"
                >
                  {{ child.name }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 结果区 -->
      <main class="results-area">
        <div v-if="loading && results.length === 0" class="loading-more">搜索中...</div>
        <div v-else-if="searched && results.length === 0" class="empty-state">
          <div class="icon">🔍</div>
          <p>未找到匹配的题目</p>
          <p class="form-hint">试试减少筛选条件或使用其他关键词</p>
        </div>
        <div v-else-if="results.length > 0">
          <p class="result-count">找到 {{ total }} 条结果</p>
          <div class="question-grid">
            <QuestionCard
              v-for="q in results"
              :key="q.id"
              :question="q"
              @click="$router.push(`/questions/${q.id}`)"
            />
          </div>
          <div v-if="hasMore" class="loading-more" @click="loadMore">
            {{ loading ? '加载中...' : '加载更多' }}
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SearchBar from '@/components/SearchBar.vue'
import QuestionCard from '@/components/QuestionCard.vue'
import { searchQuestions, aiTranslate } from '@/api'
import { useTagStore } from '@/stores/tag'
import { useToast } from '@/composables/useToast'
import type { Question, SystemTag } from '@/types'

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
const sidebarOpen = ref(false)
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
  return result
}

function countSelectedIn(cat: SystemTag): string {
  if (!cat.children) return ''
  const count = cat.children.filter(c => filterSystemTagIds.value.includes(c.id)).length
  return count > 0 ? `${count}` : ''
}

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  expandedIds.value = new Set(expandedIds.value)
}

function selectAllInCat(cat: SystemTag, select: boolean) {
  if (!cat.children) return
  for (const child of cat.children) {
    const idx = filterSystemTagIds.value.indexOf(child.id)
    if (select && idx === -1) {
      filterSystemTagIds.value.push(child.id)
    } else if (!select && idx !== -1) {
      filterSystemTagIds.value.splice(idx, 1)
    }
  }
  doSearch()
}

function handleTagToggle(node: SystemTag) {
  const idx = filterSystemTagIds.value.indexOf(node.id)
  if (idx === -1) {
    filterSystemTagIds.value.push(node.id)
  } else {
    filterSystemTagIds.value.splice(idx, 1)
  }
  doSearch()
}

function removeSystemTag(tag: SystemTag) {
  filterSystemTagIds.value = filterSystemTagIds.value.filter((id) => id !== tag.id)
  doSearch()
}

function clearAllTags() {
  filterSystemTagIds.value = []
  doSearch()
}

async function handleSearch(params: { keyword: string; searchScope: string; searchRange: string }) {
  if (!params.keyword.trim() && filterSystemTagIds.value.length === 0) {
    toast.show('请输入搜索关键词或选择标签')
    return
  }
  searchScope.value = params.searchScope as any
  searchRange.value = params.searchRange as any
  doSearch()
}

function doSearch() {
  page.value = 1
  loading.value = true
  searched.value = true
  aiSuggest.value = ''

  lastSearchParams.value = {
    keyword: searchKeyword.value,
    searchScope: searchScope.value,
    searchRange: searchRange.value,
    systemTagIds: filterSystemTagIds.value.length > 0 ? [...filterSystemTagIds.value] : undefined,
  }

  searchQuestions({
    ...lastSearchParams.value,
    page: 1,
    pageSize,
  }).then(res => {
    results.value = res.items
    total.value = res.total
    hasMore.value = res.items.length < res.total
  }).catch(() => {
    toast.show('搜索失败')
  }).finally(() => {
    loading.value = false
  })
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
    doSearch()
  } catch {
    toast.show('AI 搜索暂不可用，使用原词搜索')
    doSearch()
  }
}

onMounted(async () => {
  try {
    await tagStore.fetchSystemTags()
  } catch { /* */ }
  // 默认展开第一个分类
  if (tagStore.systemTags.length > 0) {
    expandedIds.value.add(tagStore.systemTags[0].id)
  }
})
</script>

<style scoped>
/* 复用与 QuestionList 相同的侧边栏样式 */
.browse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 0;
}
.browse-header h1 { font-size: 22px; font-weight: 700; }
.filter-toggle { position: relative; }
.filter-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; border-radius: 9px;
  background: var(--primary); color: #fff; font-size: 11px;
  font-weight: 600; margin-left: 4px; padding: 0 5px;
}

.search-row { padding: 12px 20px; }

.ai-suggestion {
  margin: 0 20px 10px; padding: 10px 14px;
  background: linear-gradient(135deg, #faf5ff, #ede9fe);
  border-radius: var(--radius); font-size: 14px;
  color: var(--primary-dark); display: flex; align-items: center; gap: 8px;
}
.ai-icon { font-size: 18px; }

.active-filters {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  padding: 0 20px 10px;
}
.filter-hint { font-size: 12px; color: var(--gray-400); margin-right: 4px; }
.filter-chip {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 4px 10px; border-radius: 14px; font-size: 12px;
  cursor: pointer; transition: all .12s;
}
.filter-chip--system { background: #ede9fe; color: #7c3aed; }
.filter-chip:hover { filter: brightness(.95); }
.chip-x { font-size: 15px; font-weight: 600; opacity: .5; }
.filter-clear { font-size: 12px; color: var(--gray-500); }

/* 侧边栏 */
.browse-body { display: flex; flex: 1; position: relative; overflow: hidden; }
.sidebar {
  position: fixed; top: 0; left: 0; bottom: 0;
  width: 280px; max-width: 85vw; background: #fff;
  z-index: 100; transform: translateX(-100%);
  transition: transform .25s cubic-bezier(.4,0,.2,1);
  display: flex; flex-direction: column;
  box-shadow: var(--shadow-lg); overflow: hidden;
}
.sidebar--open { transform: translateX(0); }
.sidebar-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 99; }
.sidebar-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 16px 12px; border-bottom: 1px solid var(--gray-100);
}
.sidebar-title { font-size: 16px; font-weight: 600; }
.sidebar-section { flex: 1; overflow-y: auto; padding: 12px 14px; }
.sidebar-section-title { font-size: 13px; font-weight: 600; color: var(--gray-600); margin-bottom: 10px; text-transform: uppercase; letter-spacing: .3px; }
.sidebar-loading { font-size: 13px; color: var(--gray-400); padding: 8px 0; }

.tag-category-list { display: flex; flex-direction: column; gap: 2px; }
.category-header {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 6px; cursor: pointer; border-radius: var(--radius-sm); user-select: none;
}
.category-header:hover { background: var(--gray-50); }
.category-arrow {
  font-size: 9px; color: var(--gray-400); transition: transform .15s;
  width: 14px; text-align: center; flex-shrink: 0;
}
.category-arrow.expanded { transform: rotate(90deg); }
.category-name { font-size: 14px; font-weight: 500; color: var(--gray-700); flex: 1; }
.category-count {
  font-size: 11px; color: var(--primary); font-weight: 600;
  background: #ede9fe; padding: 1px 6px; border-radius: 8px;
}
.category-children { padding: 4px 0 8px 20px; display: flex; flex-wrap: wrap; gap: 6px; }

.tag-quick-btn {
  font-size: 11px; padding: 2px 8px; border: 1px solid var(--gray-200);
  border-radius: 10px; background: #fff; color: var(--gray-500); cursor: pointer;
}
.tag-quick-btn--clear { color: var(--gray-400); }
.tag-quick-btn:hover { border-color: var(--primary-light); color: var(--primary); }

.tag-chip {
  display: inline-block; padding: 5px 10px; font-size: 13px;
  border-radius: 6px; border: 1.5px solid var(--gray-200);
  background: #fff; color: var(--gray-600);
  cursor: pointer; transition: all .12s; user-select: none;
}
.tag-chip:hover { border-color: var(--primary-light); background: #faf5ff; }
.tag-chip--active { border-color: var(--primary); background: var(--primary); color: #fff; font-weight: 500; }

.results-area { flex: 1; padding: 0 20px; min-height: 0; }
.result-count { font-size: 13px; color: var(--gray-500); margin-bottom: 10px; }
.question-grid { display: flex; flex-direction: column; gap: 10px; }

@media (min-width: 768px) {
  .sidebar {
    position: static; width: 240px; max-width: none;
    transform: none; box-shadow: none;
    border-right: 1px solid var(--gray-100); flex-shrink: 0;
  }
  .sidebar-header { display: none; }
  .sidebar-overlay { display: none; }
  .filter-toggle { display: none; }
  .question-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
  }
}
</style>
