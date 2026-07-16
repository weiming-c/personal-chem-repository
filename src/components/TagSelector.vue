<template>
  <div class="tag-selector">
    <!-- 已选标签展示 -->
    <div class="selected-tags" v-if="selectedSystemTags.length > 0 || selectedUserTags.length > 0">
      <span
        v-for="t in selectedSystemTags"
        :key="'s-' + t.id"
        class="tag tag-system"
      >
        {{ t.name }}
        <button class="tag-remove" @click="removeSystemTag(t)">×</button>
      </span>
      <span
        v-for="t in selectedUserTags"
        :key="'u-' + t.id"
        class="tag tag-user"
      >
        {{ t.name }}
        <button class="tag-remove" @click="removeUserTag(t)">×</button>
      </span>
    </div>

    <!-- 操作按钮 -->
    <div class="tag-actions">
      <button class="btn btn-sm btn-outline" @click="showSystemModal = true">
        选择系统标签
      </button>
      <button class="btn btn-sm btn-outline" @click="showUserModal = true">
        选择自定义标签
      </button>
    </div>

    <!-- 系统标签弹窗 -->
    <teleport to="body">
      <div v-if="showSystemModal" class="modal-overlay" @click.self="showSystemModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <span>选择系统标签</span>
            <button class="btn btn-sm btn-ghost" @click="showSystemModal = false">关闭</button>
          </div>
          <div class="modal-body">
            <div v-if="systemTagsLoading" class="loading-more">加载中...</div>
            <TagTree
              v-else
              :nodes="systemTags"
              :selectedIds="selectedSystemIds"
              :expandedIds="expandedIds"
              @toggle-select="handleSystemToggle"
              @toggle-expand="handleExpand"
            />
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary btn-block" @click="showSystemModal = false">
              确定 ({{ selectedSystemTags.length }})
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- 用户标签弹窗 -->
    <teleport to="body">
      <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <span>选择自定义标签</span>
            <button class="btn btn-sm btn-ghost" @click="showUserModal = false">关闭</button>
          </div>
          <div class="modal-body">
            <!-- 新建标签输入 -->
            <div class="new-tag-input">
              <input
                v-model="newTagName"
                class="form-input"
                placeholder="输入新标签名称"
                @keyup.enter="handleCreateTag"
              />
              <button class="btn btn-sm btn-primary" :disabled="!newTagName.trim()" @click="handleCreateTag">
                新建
              </button>
            </div>
            <!-- 已有标签列表 -->
            <div class="user-tag-list" v-if="userTags.length > 0">
              <label
                v-for="t in userTags"
                :key="t.id"
                class="user-tag-item"
                :class="{ checked: selectedUserIds.includes(t.id) }"
              >
                <input
                  type="checkbox"
                  :checked="selectedUserIds.includes(t.id)"
                  @change="toggleUserTag(t)"
                />
                <span>{{ t.name }}</span>
              </label>
            </div>
            <div v-else class="empty-state">
              <p>暂无自定义标签</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-primary btn-block" @click="showUserModal = false">
              确定 ({{ selectedUserTags.length }})
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { SystemTag, UserTag } from '@/types'
import TagTree from './TagTree.vue'
import { useTagStore } from '@/stores/tag'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  modelSystemTagIds: number[]
  modelUserTagIds: number[]
}>()

const emit = defineEmits<{
  'update:modelSystemTagIds': [ids: number[]]
  'update:modelUserTagIds': [ids: number[]]
}>()

const tagStore = useTagStore()
const toast = useToast()

const showSystemModal = ref(false)
const showUserModal = ref(false)
const newTagName = ref('')
const systemTagsLoading = ref(false)

const selectedSystemIds = ref<number[]>([...props.modelSystemTagIds])
const selectedUserIds = ref<number[]>([...props.modelUserTagIds])
const expandedIds = ref(new Set<number>())

const systemTags = computed(() => tagStore.systemTags)
const userTags = computed(() => tagStore.userTags)

const selectedSystemTags = computed(() => {
  return findSystemTags(systemTags.value, selectedSystemIds.value)
})

const selectedUserTags = computed(() => {
  return userTags.value.filter((t) => selectedUserIds.value.includes(t.id))
})

function findSystemTags(nodes: SystemTag[], ids: number[]): SystemTag[] {
  let result: SystemTag[] = []
  for (const node of nodes) {
    if (ids.includes(node.id)) result.push(node)
    if (node.children) {
      result = result.concat(findSystemTags(node.children, ids))
    }
  }
  return result
}

function handleSystemToggle(node: SystemTag) {
  const idx = selectedSystemIds.value.indexOf(node.id)
  if (idx === -1) {
    selectedSystemIds.value.push(node.id)
  } else {
    selectedSystemIds.value.splice(idx, 1)
  }
  emit('update:modelSystemTagIds', [...selectedSystemIds.value])
}

function handleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

function removeSystemTag(tag: SystemTag) {
  selectedSystemIds.value = selectedSystemIds.value.filter((id) => id !== tag.id)
  emit('update:modelSystemTagIds', [...selectedSystemIds.value])
}

function removeUserTag(tag: UserTag) {
  selectedUserIds.value = selectedUserIds.value.filter((id) => id !== tag.id)
  emit('update:modelUserTagIds', [...selectedUserIds.value])
}

function toggleUserTag(tag: UserTag) {
  const idx = selectedUserIds.value.indexOf(tag.id)
  if (idx === -1) {
    selectedUserIds.value.push(tag.id)
  } else {
    selectedUserIds.value.splice(idx, 1)
  }
  emit('update:modelUserTagIds', [...selectedUserIds.value])
}

async function handleCreateTag() {
  const name = newTagName.value.trim()
  if (!name) return
  if (userTags.value.some((t) => t.name === name)) {
    toast.show('标签已存在')
    return
  }
  try {
    const tag = await tagStore.addUserTag(name)
    selectedUserIds.value.push(tag.id)
    emit('update:modelUserTagIds', [...selectedUserIds.value])
    newTagName.value = ''
  } catch {
    toast.show('创建标签失败')
  }
}

onMounted(async () => {
  systemTagsLoading.value = true
  await tagStore.fetchSystemTags()
  await tagStore.fetchUserTags()
  systemTagsLoading.value = false
})
</script>

<style scoped>
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.tag-remove {
  margin-left: 4px;
  cursor: pointer;
  background: none;
  border: none;
  color: inherit;
  font-size: 14px;
  opacity: .6;
  line-height: 1;
}

.tag-remove:hover {
  opacity: 1;
}

.tag-actions {
  display: flex;
  gap: 8px;
}

.new-tag-input {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.new-tag-input input {
  flex: 1;
}

.user-tag-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 40vh;
  overflow-y: auto;
}

.user-tag-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.user-tag-item:hover,
.user-tag-item.checked {
  background: var(--gray-50);
}

.user-tag-item input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
}

.modal-footer {
  padding: 12px 20px;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
}
</style>
