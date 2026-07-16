<template>
  <div class="tag-manage-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>标签管理</h1>
    </div>
    <div class="page-body">
      <!-- 系统标签 -->
      <div class="section">
        <div class="section-header">
          <h2>系统预设标签</h2>
          <span class="form-hint">只读</span>
        </div>
        <div v-if="!tagStore.systemTagsLoaded" class="loading-more">加载中...</div>
        <div v-else class="tag-tree-readonly">
          <div v-for="n in tagStore.systemTags" :key="n.id" class="tree-nodes">
            <div class="tree-l1">{{ n.name }}</div>
            <div v-if="n.children" class="tree-children">
              <div v-for="c in n.children" :key="c.id" class="tree-l2">
                {{ c.name }}
                <div v-if="c.children" class="tree-l3-list">
                  <span v-for="g in c.children" :key="g.id" class="tag tag-system">{{ g.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 自定义标签 -->
      <div class="section">
        <div class="section-header">
          <h2>自定义标签</h2>
        </div>
        <!-- 新建 -->
        <div class="new-tag-row">
          <input v-model="newTagName" class="form-input" placeholder="输入标签名..." @keyup.enter="handleCreate" />
          <button class="btn btn-primary btn-sm" :disabled="!newTagName.trim()" @click="handleCreate">新建</button>
        </div>
        <!-- 列表 -->
        <div v-if="tagStore.userTags.length === 0" class="empty-state">
          <p>暂无自定义标签，创建一个吧</p>
        </div>
        <div v-else class="user-tags-list">
          <div v-for="t in tagStore.userTags" :key="t.id" class="user-tag-row">
            <span class="tag tag-user">{{ t.name }}</span>
            <span class="tag-count" v-if="t.questionCount !== undefined">{{ t.questionCount }} 题</span>
            <button class="btn btn-sm btn-ghost tag-del" @click="handleDelete(t)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTagStore } from '@/stores/tag'
import { useToast } from '@/composables/useToast'
import type { UserTag } from '@/types'

const tagStore = useTagStore()
const toast = useToast()
const newTagName = ref('')

async function handleCreate() {
  const name = newTagName.value.trim()
  if (!name) return
  if (tagStore.userTags.some(t => t.name === name)) {
    toast.show('标签已存在')
    return
  }
  try {
    await tagStore.addUserTag(name)
    newTagName.value = ''
    toast.show('标签已创建')
  } catch { toast.show('创建失败') }
}

async function handleDelete(tag: UserTag) {
  try {
    await tagStore.removeUserTag(tag.id)
    toast.show('已删除')
  } catch { toast.show('删除失败') }
}

onMounted(async () => {
  await tagStore.fetchSystemTags()
  await tagStore.fetchUserTags()
})
</script>

<style scoped>
.section { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-header h2 { font-size: 16px; font-weight: 600; }
.tree-l1 { font-weight: 600; font-size: 15px; padding: 10px 0; color: var(--gray-800); border-bottom: 1px solid var(--gray-100); }
.tree-l2 { font-size: 14px; padding: 8px 12px; color: var(--gray-700); }
.tree-l3-list { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; padding-left: 8px; }
.new-tag-row { display: flex; gap: 8px; margin-bottom: 12px; }
.new-tag-row input { flex: 1; }
.user-tag-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--gray-50); }
.tag-count { font-size: 12px; color: var(--gray-400); }
.tag-del { margin-left: auto; color: var(--danger); }
</style>
