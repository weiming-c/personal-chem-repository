<template>
  <div class="browse-page">
    <!-- 顶栏 -->
    <div class="browse-header">
      <h1>题库</h1>
      <div class="browse-header-actions">
        <button class="btn btn-sm btn-ghost filter-toggle" @click="sidebarOpen = !sidebarOpen">
          🏷️ 标签
          <span v-if="activeFilterCount > 0" class="filter-count">{{ activeFilterCount }}</span>
        </button>
        <router-link to="/questions/new" class="btn btn-sm btn-primary">录入</router-link>
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="search-row">
      <input
        v-model.trim="searchKeyword"
        class="form-input search-input"
        placeholder="搜索题干或答案..."
        @input="onSearchInput"
        @keyup.enter="loadQuestions()"
      />
      <select v-model="filterSource" class="form-input source-select" @change="loadQuestions()">
        <option value="">全部来源</option>
        <option value="private">私有</option>
        <option value="public">公共</option>
      </select>
    </div>

    <!-- 已选筛选标签 -->
    <div v-if="activeFilterCount > 0" class="active-filters">
      <span class="filter-hint">筛选：</span>
      <span
        v-for="tag in selectedSystemTagObjs"
        :key="'s-' + tag.id"
        class="filter-chip filter-chip--system"
        @click="toggleSystemTag(tag)"
      >
        {{ tag.name }} <span class="chip-x">×</span>
      </span>
      <span
        v-for="tag in selectedUserTagObjs"
        :key="'u-' + tag.id"
        class="filter-chip filter-chip--user"
        @click="toggleUserTag(tag)"
      >
        {{ tag.name }} <span class="chip-x">×</span>
      </span>
      <button class="btn btn-sm btn-ghost filter-clear" @click="clearAllFilters">清除</button>
    </div>

    <!-- 主体：侧边栏 + 内容 -->
    <div class="browse-body">
      <!-- 遮罩（移动端） -->
      <div
        v-if="sidebarOpen"
        class="sidebar-overlay"
        @click="sidebarOpen = false"
      ></div>

      <!-- 侧边栏 -->
      <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
        <div class="sidebar-header">
          <span class="sidebar-title">标签筛选</span>
          <button class="btn btn-sm btn-ghost" @click="sidebarOpen = false">✕</button>
        </div>

        <!-- 系统标签 -->
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
                <span class="category-arrow" :class="{ expanded: expandedCats.has(cat.id) }">▶</span>
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">{{ countSelectedIn(cat) }}</span>
              </div>
              <div v-if="cat.children && expandedCats.has(cat.id)" class="category-children">
                <!-- 全选/不选快捷按钮 -->
                <button
                  class="tag-quick-btn"
                  @click="selectAllInCategory(cat, true)"
                >全选</button>
                <button
                  class="tag-quick-btn tag-quick-btn--clear"
                  @click="selectAllInCategory(cat, false)"
                >清除</button>
                <div
                  v-for="child in cat.children"
                  :key="child.id"
                  class="tag-chip"
                  :class="{ 'tag-chip--active': selectedSystemIds.has(child.id) }"
                  @click="toggleSystemTag(child)"
                >
                  {{ child.name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 用户标签 -->
        <div class="sidebar-section">
          <h3 class="sidebar-section-title">👤 自定义标签</h3>
          <div v-if="tagStore.userTags.length === 0" class="sidebar-empty">
            暂无自定义标签
          </div>
          <div v-else class="tag-chip-list">
            <div
              v-for="tag in tagStore.userTags"
              :key="tag.id"
              class="tag-chip"
              :class="{ 'tag-chip--active': selectedUserIds.has(tag.id) }"
              @click="toggleUserTag(tag)"
            >
              {{ tag.name }}
              <span v-if="tag.questionCount" class="chip-sub">({{ tag.questionCount }})</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 结果区 -->
      <main class="results-area">
        <!-- 加载 -->
        <div v-if="loading && questions.length === 0" class="loading-more">加载中...</div>

        <!-- 空态 -->
        <div v-else-if="questions.length === 0" class="empty-state">
          <div class="icon">📚</div>
          <p>暂无题目</p>
          <p v-if="activeFilterCount > 0" class="form-hint">试试减少筛选条件</p>
        </div>

        <!-- 列表 -->
        <div v-else class="question-grid">
          <QuestionCard
            v-for="q in questions"
            :key="q.id"
            :question="q"
            @click="$router.push(`/questions/${q.id}`)"
          />
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
import QuestionCard from '@/components/QuestionCard.vue'
import { getQuestions } from '@/api'
import type { Question, SystemTag, UserTag } from '@/types'
import { useTagStore } from '@/stores/tag'

const tagStore = useTagStore()

// ------- 状态 -------
const questions = ref<Question[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const pageSize = 20
const hasMore = ref(false)

const searchKeyword = ref('')
const filterSource = ref('')
const selectedSystemIds = ref(new Set<number>())
const selectedUserIds = ref(new Set<number>())
const sidebarOpen = ref(false)
const expandedCats = ref(new Set<number>())

let searchTimer: ReturnType<typeof setTimeout> | null = null

// ------- 计算 -------
const activeFilterCount = computed(() => selectedSystemIds.value.size + selectedUserIds.value.size)

// 通过 ID 找到标签对象
const selectedSystemTagObjs = computed(() => {
  return findTagsByIds(tagStore.systemTags, [...selectedSystemIds.value])
})

const selectedUserTagObjs = computed(() => {
  return tagStore.userTags.filter(t => selectedUserIds.value.has(t.id))
})

function findTagsByIds(nodes: SystemTag[], ids: number[]): SystemTag[] {
  const result: SystemTag[] = []
  for (const n of nodes) {
    if (ids.includes(n.id)) result.push(n)
    if (n.children) result.push(...findTagsByIds(n.children, ids))
  }
  return result
}

function countSelectedIn(cat: SystemTag): string {
  if (!cat.children) return ''
  const count = cat.children.filter(c => selectedSystemIds.value.has(c.id)).length
  return count > 0 ? `${count}` : ''
}

// ------- 标签操作 -------
function toggleSystemTag(tag: SystemTag) {
  if (selectedSystemIds.value.has(tag.id)) {
    selectedSystemIds.value.delete(tag.id)
  } else {
    selectedSystemIds.value.add(tag.id)
  }
  // 触发响应式
  selectedSystemIds.value = new Set(selectedSystemIds.value)
  loadQuestions()
}

function toggleUserTag(tag: UserTag) {
  if (selectedUserIds.value.has(tag.id)) {
    selectedUserIds.value.delete(tag.id)
  } else {
    selectedUserIds.value.add(tag.id)
  }
  selectedUserIds.value = new Set(selectedUserIds.value)
  loadQuestions()
}

function toggleExpand(id: number) {
  if (expandedCats.value.has(id)) {
    expandedCats.value.delete(id)
  } else {
    expandedCats.value.add(id)
  }
  expandedCats.value = new Set(expandedCats.value)
}

function selectAllInCategory(cat: SystemTag, select: boolean) {
  if (!cat.children) return
  for (const child of cat.children) {
    if (select) {
      selectedSystemIds.value.add(child.id)
    } else {
      selectedSystemIds.value.delete(child.id)
    }
  }
  selectedSystemIds.value = new Set(selectedSystemIds.value)
  loadQuestions()
}

function clearAllFilters() {
  selectedSystemIds.value = new Set()
  selectedUserIds.value = new Set()
  searchKeyword.value = ''
  filterSource.value = ''
  loadQuestions()
}

// 搜索防抖
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadQuestions()
  }, 400)
}

// ------- 数据加载 -------
function buildParams(pageNum: number) {
  const params: any = { page: pageNum, pageSize }

  if (selectedSystemIds.value.size > 0) {
    params.system_tag_ids = [...selectedSystemIds.value].join(',')
  }
  if (selectedUserIds.value.size > 0) {
    params.user_tag_ids = [...selectedUserIds.value].join(',')
  }
  if (filterSource.value) {
    params.source = filterSource.value
  }
  if (searchKeyword.value) {
    params.keyword = searchKeyword.value
  }

  return params
}

async function loadQuestions() {
  loading.value = true
  page.value = 1
  try {
    const res = await getQuestions(buildParams(1))
    questions.value = res.items
    total.value = res.total
    hasMore.value = res.items.length < res.total
  } catch {
    // 静默处理
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value || !hasMore.value) return
  loading.value = true
  page.value++
  try {
    const res = await getQuestions(buildParams(page.value))
    questions.value.push(...res.items)
    hasMore.value = questions.value.length < res.total
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      tagStore.fetchSystemTags(),
      tagStore.fetchUserTags(),
    ])
  } catch {
    // 标签加载失败不影响题目列表
  }
  // 默认展开第一个分类
  if (tagStore.systemTags.length > 0) {
    expandedCats.value.add(tagStore.systemTags[0].id)
  }
  await loadQuestions()
})
</script>

<style scoped>
/* ====== 布局 ====== */
.browse-page {
  padding-bottom: 80px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.browse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 0;
}

.browse-header h1 {
  font-size: 22px;
  font-weight: 700;
}

.browse-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-toggle {
  position: relative;
}

.filter-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background: var(--primary);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
  padding: 0 5px;
}

/* ====== 搜索行 ====== */
.search-row {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
}

.search-input {
  flex: 1;
  font-size: 14px;
}

.source-select {
  width: 110px;
  font-size: 14px;
  flex-shrink: 0;
}

/* ====== 已选筛选标签条 ====== */
.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding: 0 20px 10px;
}

.filter-hint {
  font-size: 12px;
  color: var(--gray-400);
  margin-right: 4px;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all .12s;
}

.filter-chip--system {
  background: #ede9fe;
  color: #7c3aed;
}

.filter-chip--user {
  background: #fef3c7;
  color: #d97706;
}

.filter-chip:hover {
  filter: brightness(.95);
}

.chip-x {
  font-size: 15px;
  font-weight: 600;
  opacity: .5;
}

.filter-clear {
  font-size: 12px;
  color: var(--gray-500);
}

/* ====== 主体 ====== */
.browse-body {
  display: flex;
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* ====== 侧边栏 ====== */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  max-width: 85vw;
  background: #fff;
  z-index: 100;
  transform: translateX(-100%);
  transition: transform .25s cubic-bezier(.4,0,.2,1);
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.sidebar--open {
  transform: translateX(0);
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 99;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--gray-100);
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
}

/* 侧边栏可滚动内容 */
.sidebar-section {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
}

.sidebar-section + .sidebar-section {
  border-top: 1px solid var(--gray-100);
  flex: none;
  max-height: 40%;
  overflow-y: auto;
}

.sidebar-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-600);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: .3px;
}

.sidebar-loading,
.sidebar-empty {
  font-size: 13px;
  color: var(--gray-400);
  padding: 8px 0;
}

/* ====== 分类区块 ====== */
.tag-category-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.tag-category {
  border-radius: var(--radius-sm);
}

.category-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 6px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  user-select: none;
}

.category-header:hover {
  background: var(--gray-50);
}

.category-arrow {
  font-size: 9px;
  color: var(--gray-400);
  transition: transform .15s;
  width: 14px;
  text-align: center;
  flex-shrink: 0;
}

.category-arrow.expanded {
  transform: rotate(90deg);
}

.category-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  flex: 1;
}

.category-count {
  font-size: 11px;
  color: var(--primary);
  font-weight: 600;
  background: #ede9fe;
  padding: 1px 6px;
  border-radius: 8px;
}

.category-children {
  padding: 4px 0 8px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 全选/清除快捷按钮 */
.tag-quick-btn {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid var(--gray-200);
  border-radius: 10px;
  background: #fff;
  color: var(--gray-500);
  cursor: pointer;
}

.tag-quick-btn--clear {
  color: var(--gray-400);
}

.tag-quick-btn:hover {
  border-color: var(--primary-light);
  color: var(--primary);
}

/* ====== 标签小方块 ====== */
.tag-chip {
  display: inline-block;
  padding: 5px 10px;
  font-size: 13px;
  border-radius: 6px;
  border: 1.5px solid var(--gray-200);
  background: #fff;
  color: var(--gray-600);
  cursor: pointer;
  transition: all .12s;
  user-select: none;
}

.tag-chip:hover {
  border-color: var(--primary-light);
  background: #faf5ff;
}

.tag-chip--active {
  border-color: var(--primary);
  background: var(--primary);
  color: #fff;
  font-weight: 500;
}

.chip-sub {
  font-size: 11px;
  opacity: .7;
}

.tag-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ====== 结果区 ====== */
.results-area {
  flex: 1;
  padding: 0 20px;
  min-height: 0;
}

.question-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ====== 桌面端适配 ====== */
@media (min-width: 768px) {
  .browse-page {
    max-width: 960px;
    margin: 0 auto;
  }

  .sidebar {
    position: static;
    width: 240px;
    max-width: none;
    transform: none;
    box-shadow: none;
    border-right: 1px solid var(--gray-100);
    flex-shrink: 0;
  }

  .sidebar-header {
    display: none;
  }

  .sidebar-overlay {
    display: none;
  }

  .filter-toggle {
    display: none;
  }

  .question-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
  }
}
</style>
