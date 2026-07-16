<template>
  <div class="paper-config-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>智能组卷</h1>
    </div>
    <div class="page-body">
      <div class="form-group">
        <label class="form-label">试卷名称</label>
        <input v-model="paperName" class="form-input" placeholder="如：有机化学专项练习" />
      </div>
      <div class="form-group">
        <label class="form-label">描述（可选）</label>
        <input v-model="paperDesc" class="form-input" placeholder="可选" />
      </div>
      <div class="form-group">
        <label class="form-label">题目来源</label>
        <div class="radio-group">
          <label class="radio-card" :class="{ active: sourceMode === 'private' }">
            <input type="radio" v-model="sourceMode" value="private" />私有题库
          </label>
          <label class="radio-card" :class="{ active: sourceMode === 'mixed' }">
            <input type="radio" v-model="sourceMode" value="mixed" />混合模式
          </label>
          <label class="radio-card" :class="{ active: sourceMode === 'public' }">
            <input type="radio" v-model="sourceMode" value="public" />仅公共题库
          </label>
        </div>
      </div>

      <!-- 筛选条件 -->
      <div class="form-group">
        <label class="form-label">系统标签筛选</label>
        <div class="selected-tags" v-if="selectedSystemTags.length > 0">
          <span v-for="t in selectedSystemTags" :key="t.id" class="tag tag-system">{{ t.name }}
            <button class="tag-remove" @click="removeSystemTag(t)">×</button>
          </span>
        </div>
        <button class="btn btn-outline btn-block" @click="showTagModal = true">选择知识点</button>
      </div>

      <div class="form-group">
        <label class="form-label">仅限错题</label>
        <label class="switch-label">
          <input type="checkbox" v-model="wrongOnly" />
          <span class="switch-track"><span class="switch-thumb"></span></span>
          <span>{{ wrongOnly ? '仅从错题中选题' : '从全部题目中选题' }}</span>
        </label>
      </div>

      <div class="form-group">
        <label class="form-label">题目数量</label>
        <input v-model.number="questionCount" type="number" class="form-input" min="1" max="100" />
      </div>

      <div class="form-group">
        <label class="switch-label">
          <input type="checkbox" v-model="randomOrder" />
          <span class="switch-track"><span class="switch-thumb"></span></span>
          <span>随机排序</span>
        </label>
      </div>

      <button class="btn btn-primary btn-block" :disabled="generating" @click="handleGenerate">
        {{ generating ? '生成中...' : '生成试卷' }}
      </button>

      <!-- 预览 -->
      <div v-if="previewQuestions.length > 0" class="preview-section">
        <h3>预览 ({{ previewQuestions.length }} 题)</h3>
        <div v-for="(q, i) in previewQuestions" :key="q.id" class="preview-item">
          <span class="preview-num">{{ i + 1 }}</span>
          <span class="preview-text">{{ truncate(q.content, 60) }}</span>
          <span class="preview-tag">{{ q.source === 'public' ? '公共' : '私有' }}</span>
        </div>
        <button class="btn btn-success btn-block" @click="handleSave">保存试卷</button>
      </div>
    </div>

    <!-- 标签弹窗 -->
    <teleport to="body">
      <div v-if="showTagModal" class="modal-overlay" @click.self="showTagModal = false">
        <div class="modal-content">
          <div class="modal-header"><span>选择知识点</span><button class="btn btn-sm btn-ghost" @click="showTagModal=false">关闭</button></div>
          <div class="modal-body">
            <TagTree :nodes="tagStore.systemTags" :selectedIds="filterTagIds" :expandedIds="expandedIds"
              @toggle-select="handleTagToggle" @toggle-expand="handleExpand" />
            <button class="btn btn-primary btn-block" style="margin-top:12px" @click="showTagModal=false">确定</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TagTree from '@/components/TagTree.vue'
import { useTagStore } from '@/stores/tag'
import { usePaperStore } from '@/stores/paper'
import { useToast } from '@/composables/useToast'
import { getQuestions, getWrongQuestions } from '@/api'
import type { SystemTag, Question } from '@/types'

const router = useRouter()
const tagStore = useTagStore()
const paperStore = usePaperStore()
const toast = useToast()

const paperName = ref('')
const paperDesc = ref('')
const sourceMode = ref<'private' | 'public' | 'mixed'>('private')
const wrongOnly = ref(false)
const questionCount = ref(10)
const randomOrder = ref(true)
const filterTagIds = ref<number[]>([])
const showTagModal = ref(false)
const expandedIds = ref(new Set<number>())
const generating = ref(false)
const previewQuestions = ref<Question[]>([])

const selectedSystemTags = computed(() => findTags(tagStore.systemTags, filterTagIds.value).slice(0, 5))

function findTags(nodes: SystemTag[], ids: number[]): SystemTag[] {
  let r: SystemTag[] = []
  for (const n of nodes) {
    if (ids.includes(n.id)) r.push(n)
    if (n.children) r = r.concat(findTags(n.children, ids))
  }
  return r
}

function handleTagToggle(node: SystemTag) {
  const i = filterTagIds.value.indexOf(node.id)
  i === -1 ? filterTagIds.value.push(node.id) : filterTagIds.value.splice(i, 1)
}

function handleExpand(id: number) {
  expandedIds.value.has(id) ? expandedIds.value.delete(id) : expandedIds.value.add(id)
}

function removeSystemTag(tag: SystemTag) {
  filterTagIds.value = filterTagIds.value.filter(id => id !== tag.id)
}

function truncate(t: string, len: number) {
  return t && t.length > len ? t.slice(0, len) + '...' : (t || '')
}

async function handleGenerate() {
  if (!paperName.value.trim()) { toast.show('请输入试卷名称'); return }
  generating.value = true
  try {
    let questions: Question[] = []
    if (wrongOnly.value) {
      const res = await getWrongQuestions({ page: 1, pageSize: questionCount.value, status: 'active' })
      const ids = res.items.map(w => w.questionId).filter(Boolean) as number[]
      // Fetch each question
      const qs = await Promise.all(ids.map(id => getQuestions({ page: 1, pageSize: 1 }).then(() => {
        // We need each question; for now we mock the preview
        return null
      })))
      questions = qs.filter(Boolean) as Question[]
    } else {
      const params: any = { page: 1, pageSize: questionCount.value }
      if (filterTagIds.value.length > 0) params.systemTagIds = filterTagIds.value
      if (sourceMode.value !== 'mixed') params.source = sourceMode.value
      const res = await getQuestions(params)
      questions = res.items
    }

    if (questions.length === 0) { toast.show('没有符合条件的题目'); return }

    if (randomOrder.value) {
      questions.sort(() => Math.random() - 0.5)
    }
    previewQuestions.value = questions
    toast.show(`已匹配 ${questions.length} 道题目`)
  } catch { toast.show('生成失败') } finally { generating.value = false }
}

async function handleSave() {
  try {
    const paper = await paperStore.addPaper({
      name: paperName.value,
      description: paperDesc.value,
      sourceMode: sourceMode.value,
      questionIds: previewQuestions.value.map(q => q.id),
    })
    toast.show('试卷已保存')
    router.replace(`/papers/${paper.id}/practice`)
  } catch { toast.show('保存失败') }
}

onMounted(async () => {
  await tagStore.fetchSystemTags()
})
</script>

<style scoped>
.radio-group { display: flex; flex-direction: column; gap: 8px; }
.radio-card { display: flex; align-items: center; gap: 8px; padding: 12px; border: 1.5px solid var(--gray-200); border-radius: var(--radius); cursor: pointer; font-size: 14px; }
.radio-card.active { border-color: var(--primary); background: var(--primary-bg); }
.radio-card input { accent-color: var(--primary); }
.selected-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tag-remove { margin-left: 4px; cursor: pointer; background: none; border: none; color: inherit; font-size: 14px; }
.switch-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 14px; }
.switch-track { width: 44px; height: 24px; background: var(--gray-200); border-radius: 12px; position: relative; transition: .2s; }
.switch-label input:checked + .switch-track { background: var(--primary); }
.switch-thumb { width: 20px; height: 20px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: .2s; }
.switch-label input:checked + .switch-track .switch-thumb { left: 22px; }
.switch-label input { display: none; }
.preview-section { margin-top: 24px; }
.preview-section h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.preview-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: var(--gray-50); border-radius: var(--radius-sm); margin-bottom: 6px; font-size: 14px; }
.preview-num { width: 24px; height: 24px; border-radius: 50%; background: var(--primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }
.preview-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.preview-tag { font-size: 11px; color: var(--gray-400); flex-shrink: 0; }
</style>
