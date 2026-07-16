<template>
  <div class="tag-tree">
    <template v-for="node in nodes" :key="node.id">
      <div
        class="tree-node"
        :class="{ 'tree-node--active': selectedIds.includes(node.id) }"
      >
        <div
          class="tree-node-inner"
          :style="{ paddingLeft: (node.level || 0) * 16 + 'px' }"
        >
          <span
            v-if="node.children && node.children.length > 0"
            class="tree-arrow"
            :class="{ expanded: expandedIds.has(node.id) }"
            @click.stop="$emit('toggleExpand', node.id)"
          >▶</span>
          <span v-else class="tree-arrow-placeholder"></span>
          <label class="tree-checkbox-wrapper">
            <input
              type="checkbox"
              :checked="selectedIds.includes(node.id)"
              @change="$emit('toggleSelect', node)"
            />
            <span class="tree-label">{{ node.name }}</span>
          </label>
        </div>
      </div>
      <!-- 递归渲染子节点 -->
      <TagTree
        v-if="node.children && node.children.length > 0 && expandedIds.has(node.id)"
        :nodes="node.children.map(c => ({ ...c, level: (node.level || 0) + 1 }))"
        :selectedIds="selectedIds"
        :expandedIds="expandedIds"
        @toggleSelect="(n) => $emit('toggleSelect', n)"
        @toggleExpand="(id) => $emit('toggleExpand', id)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import type { SystemTag } from '@/types'

defineProps<{
  nodes: SystemTag[]
  selectedIds: number[]
  expandedIds: Set<number>
}>()

defineEmits<{
  toggleSelect: [node: SystemTag]
  toggleExpand: [id: number]
}>()
</script>

<script lang="ts">
// 递归组件自引用
export default { name: 'TagTree' }
</script>

<style scoped>
.tag-tree {
  max-height: 50vh;
  overflow-y: auto;
}

.tree-node {
  border-bottom: 1px solid var(--gray-50);
}

.tree-node--active .tree-label {
  color: var(--primary);
  font-weight: 500;
}

.tree-node-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
}

.tree-node-inner:hover {
  background: var(--gray-50);
}

.tree-arrow {
  font-size: 10px;
  color: var(--gray-400);
  transition: transform .15s;
  width: 16px;
  text-align: center;
  flex-shrink: 0;
  cursor: pointer;
}

.tree-arrow.expanded {
  transform: rotate(90deg);
}

.tree-arrow-placeholder {
  width: 16px;
  flex-shrink: 0;
}

.tree-checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}

.tree-checkbox-wrapper input {
  width: 16px;
  height: 16px;
  accent-color: var(--primary);
  flex-shrink: 0;
}

.tree-label {
  font-size: 14px;
  color: var(--gray-700);
}
</style>
