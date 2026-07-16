<template>
  <div class="wrong-questions-page">
    <div class="page-header">
      <h1>错题本</h1>
      <button class="btn btn-sm btn-outline" @click="showFilter = !showFilter">筛选</button>
    </div>

    <div class="stats-bar">
      <div class="stat-item"><span class="stat-num">{{ stats.active }}</span><span class="stat-label">待复习</span></div>
      <div class="stat-item"><span class="stat-num mastered">{{ stats.mastered }}</span><span class="stat-label">已掌握</span></div>
      <div class="stat-item"><span class="stat-num total">{{ stats.total }}</span><span class="stat-label">累计错题</span></div>
    </div>

    <div class="filter-panel" v-if="showFilter">
      <div class="form-group">
        <label class="form-label">状态</label>
        <select v-model="filterStatus" class="form-input" @change="loadData">
          <option value="active">待复习</option><option value="mastered">已掌握</option><option value="">全部</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">错误次数</label>
        <select v-model="filterWrongCount" class="form-input" @change="loadData">
          <option value="">不限</option><option value="1">1次</option><option value="2">2-3次</option><option value="4">4次及以上</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">系统标签</label>
        <button class="btn btn-sm btn-outline btn-block" @click="showTagModal = true">
          选择 {{ filterTagIds.length ? `(${filterTagIds.length})` : '' }}
        </button>
      </div>
    </div>

    <div class="action-row" v-if="wrongItems.length > 0">
      <button class="btn btn-sm btn-primary" @click="exportToPaper">导出为错题卷</button>
    </div>

    <div class="page-body">
      <div v-if="loading && wrongItems.length === 0" class="loading-more">加载中...</div>
      <div v-else-if="wrongItems.length === 0" class="empty-state">
        <div class="icon">{{ filterStatus === 'mastered' ? '✅' : '🎉' }}</div>
        <p>{{ filterStatus === 'mastered' ? '暂无已掌握题目' : '暂无错题，太棒了！' }}</p>
      </div>
      <div v-else>
        <div v-for="wq in wrongItems" :key="wq.id" class="wrong-item card">
          <div class="wrong-header">
            <span class="wrong-count" :class="{ high: wq.wrongCount >= 3 }">错过 {{ wq.wrongCount }} 次</span>
            <span class="wrong-status" :class="'status-' + wq.status">{{ statusLabel(wq.status) }}</span>
            <span class="wrong-date">{{ formatDate(wq.lastWrongAt) }}</span>
          </div>
          <div class="wrong-preview" @click="goToQuestion(wq)">
            <p>{{ truncate(wq.question?.content || '', 100) }}</p>
          </div>
          <div class="wrong-note" v-if="wq.note || wq.wrongReason">
            <strong>笔记：</strong>{{ wq.note || wq.wrongReason }}
          </div>
          <div class="wrong-actions">
            <button class="btn btn-sm btn-outline" @click="openNoteEditor(wq)">编辑笔记</button>
            <button v-if="wq.status === 'active'" class="btn btn-sm btn-success" @click="handleMaster(wq)">已掌握</button>
            <button class="btn btn-sm btn-ghost" @click="handleRemove(wq)">移除</button>
          </div>
        </div>
        <div v-if="hasMore" class="loading-more" @click="loadMore">{{ loading ? '加载中...' : '加载更多' }}</div>
      </div>
    </div>

    <!-- 笔记弹窗 -->
    <teleport to="body">
      <div v-if="noteEditorVisible" class="modal-overlay" @click.self="noteEditorVisible = false">
        <div class="modal-content">
          <div class="modal-header"><span>编辑笔记</span><button class="btn btn-sm btn-ghost" @click="noteEditorVisible=false">关闭</button></div>
          <div class="modal-body">
            <div class="form-group"><label class="form-label">错因分析</label><textarea v-model="editingReason" class="form-textarea" rows="2"></textarea></div>
            <div class="form-group"><label class="form-label">笔记</label><textarea v-model="editingNote" class="form-textarea" rows="3"></textarea></div>
            <button class="btn btn-primary btn-block" @click="saveNote">保存</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 标签弹窗 -->
    <teleport to="body">
      <div v-if="showTagModal" class="modal-overlay" @click.self="closeTagModal">
        <div class="modal-content">
          <div class="modal-header"><span>按标签筛选</span><button class="btn btn-sm btn-ghost" @click="closeTagModal">关闭</button></div>
          <div class="modal-body">
            <TagTree :nodes="tagStore.systemTags" :selectedIds="filterTagIds" :expandedIds="expandedIds"
              @toggle-select="handleTagToggle" @toggle-expand="handleExpand" />
            <button class="btn btn-primary btn-block" style="margin-top:12px" @click="closeTagModal">确定</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TagTree from '@/components/TagTree.vue'
import { useWrongQuestionStore } from '@/stores/wrongQuestion'
import { usePaperStore } from '@/stores/paper'
import { useTagStore } from '@/stores/tag'
import { useToast } from '@/composables/useToast'
import type { WrongQuestion, SystemTag, WrongQuestionStatus } from '@/types'

const router = useRouter()
const wrongStore = useWrongQuestionStore()
const paperStore = usePaperStore()
const tagStore = useTagStore()
const toast = useToast()

const wrongItems = ref<WrongQuestion[]>([])
const loading = ref(false)
const showFilter = ref(false)
const showTagModal = ref(false)
const filterStatus = ref<WrongQuestionStatus | ''>('active')
const filterWrongCount = ref('')
const filterTagIds = ref<number[]>([])
const expandedIds = ref(new Set<number>())
const page = ref(1)
const pageSize = 20
const hasMore = ref(false)

const noteEditorVisible = ref(false)
const editingWq = ref<WrongQuestion | null>(null)
const editingReason = ref('')
const editingNote = ref('')

const stats = reactive({ active: 0, mastered: 0, total: 0 })

function statusLabel(s: string) {
  return { active: '待复习', mastered: '已掌握', removed: '已移除' }[s] || s
}

function formatDate(d: string) {
  if (!d) return ''
  const dt = new Date(d)
  return `${dt.getMonth() + 1}/${dt.getDate()}`
}

function truncate(t: string, len: number) {
  return t && t.length > len ? t.slice(0, len) + '...' : (t || '')
}

function goToQuestion(wq: WrongQuestion) {
  if (wq.questionId) router.push(`/questions/${wq.questionId}`)
}

async function loadData() {
  loading.value = true; page.value = 1
  try {
    const params: any = { page: 1, pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterWrongCount.value) {
      const n = Number(filterWrongCount.value)
      if (n >= 4) { params.wrongCountMin = 4 } else if (n === 2) { params.wrongCountMin = 2; params.wrongCountMax = 3 } else { params.wrongCountMin = 1; params.wrongCountMax = 1 }
    }
    if (filterTagIds.value.length > 0) params.systemTagIds = filterTagIds.value
    const res = await wrongStore.fetchWrongQuestions(params)
    wrongItems.value = wrongStore.wrongQuestions
    hasMore.value = wrongStore.wrongQuestions.length < wrongStore.total
  } finally { loading.value = false }
}

async function loadMore() {
  if (loading.value || !hasMore.value) return
  loading.value = true; page.value++
  try {
    const params: any = { page: page.value, pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await wrongStore.fetchWrongQuestions(params)
    wrongItems.value = wrongStore.wrongQuestions
    hasMore.value = wrongStore.wrongQuestions.length < wrongStore.total
  } finally { loading.value = false }
}

async function handleMaster(wq: WrongQuestion) {
  try {
    await wrongStore.update(wq.id, { status: 'mastered' })
    wq.status = 'mastered'
    stats.active--; stats.mastered++
    toast.show('已标记为掌握')
  } catch { toast.show('操作失败') }
}

async function handleRemove(wq: WrongQuestion) {
  try {
    await wrongStore.remove(wq.id)
    wrongItems.value = wrongItems.value.filter((x) => x.id !== wq.id)
    if (wq.status === 'active') stats.active--
    stats.total--
    toast.show('已移除')
  } catch { toast.show('操作失败') }
}

function openNoteEditor(wq: WrongQuestion) {
  editingWq.value = wq
  editingReason.value = wq.wrongReason || ''
  editingNote.value = wq.note || ''
  noteEditorVisible.value = true
}

async function saveNote() {
  if (!editingWq.value) return
  try {
    await wrongStore.update(editingWq.value.id, { wrongReason: editingReason.value, note: editingNote.value })
    editingWq.value.wrongReason = editingReason.value
    editingWq.value.note = editingNote.value
    noteEditorVisible.value = false
    toast.show('笔记已保存')
  } catch { toast.show('保存失败') }
}

async function exportToPaper() {
  const ids = wrongItems.value.filter((w) => w.status === 'active').map((w) => w.questionId)
  if (ids.length === 0) { toast.show('没有待复习的错题'); return }
  try {
    const paper = await paperStore.addPaper({
      name: `错题卷 ${new Date().toLocaleDateString()}`,
      description: '从错题本导出',
      sourceMode: 'private',
      questionIds: ids,
    })
    toast.show('试卷已生成')
    router.push(`/papers/${paper.id}/practice`)
  } catch { toast.show('生成失败') }
}

function handleTagToggle(node: SystemTag) {
  const idx = filterTagIds.value.indexOf(node.id)
  if (idx === -1) filterTagIds.value.push(node.id)
  else filterTagIds.value.splice(idx, 1)
}

function handleExpand(id: number) {
  expandedIds.value.has(id) ? expandedIds.value.delete(id) : expandedIds.value.add(id)
}

function closeTagModal() { showTagModal.value = false; loadData() }

async function fetchStats() {
  try {
    const [active, mastered, all] = await Promise.all([
      wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1, status: 'active' }),
      wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1, status: 'mastered' }),
      wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1 }),
    ])
    stats.active = wrongStore.total || 0
    await wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1, status: 'mastered' })
    stats.mastered = wrongStore.total || 0
    await wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1 })
    stats.total = wrongStore.total || 0
  } catch {}
  // Simpler approach:
  stats.active = 0; stats.mastered = 0; stats.total = 0
}

onMounted(async () => {
  await tagStore.fetchSystemTags()
  await loadData()
  // Quick stats fetch
  try {
    await wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1, status: 'active' }); stats.active = wrongStore.total
    await wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1, status: 'mastered' }); stats.mastered = wrongStore.total
    await wrongStore.fetchWrongQuestions({ page: 1, pageSize: 1 }); stats.total = wrongStore.total
  } catch {}
})
</script>

<style scoped>
.stats-bar { display: flex; padding: 12px 20px; gap: 12px; }
.stat-item { flex: 1; text-align: center; background: var(--gray-50); border-radius: var(--radius); padding: 12px 8px; }
.stat-num { display: block; font-size: 24px; font-weight: 700; color: var(--primary); }
.stat-num.mastered { color: var(--success); }
.stat-num.total { color: var(--gray-600); }
.stat-label { font-size: 12px; color: var(--gray-500); margin-top: 2px; display: block; }
.filter-panel { padding: 0 20px 12px; }
.action-row { padding: 0 20px 12px; }
.wrong-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.wrong-count { font-size: 12px; padding: 2px 8px; border-radius: 10px; background: var(--warning-bg); color: var(--warning); }
.wrong-count.high { background: var(--danger-bg); color: var(--danger); }
.wrong-status { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.status-active { background: var(--danger-bg); color: var(--danger); }
.status-mastered { background: var(--success-bg); color: var(--success); }
.wrong-date { margin-left: auto; font-size: 12px; color: var(--gray-400); }
.wrong-preview { cursor: pointer; font-size: 14px; color: var(--gray-700); margin-bottom: 8px; padding: 8px; background: var(--gray-50); border-radius: var(--radius-sm); }
.wrong-note { font-size: 13px; color: var(--gray-500); background: var(--primary-bg); padding: 8px 10px; border-radius: var(--radius-sm); margin-bottom: 8px; }
.wrong-actions { display: flex; gap: 8px; }
</style>
