<template>
  <nav class="tab-bar">
    <router-link
      v-for="tab in tabs"
      :key="tab.path"
      :to="tab.path"
      class="tab-item"
      active-class="tab-active"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
    </router-link>
  </nav>
</template>

<script setup lang="ts">
const tabs = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/questions', label: '题库', icon: '📚' },
  { path: '/search', label: '检索', icon: '🔍' },
  { path: '/wrong-questions', label: '错题', icon: '📝' },
  { path: '/papers', label: '试卷', icon: '📄' },
]
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: var(--max-width);
  display: flex;
  background: #fff;
  border-top: 1px solid var(--gray-100);
  padding-bottom: max(0px, env(safe-area-inset-bottom));
  z-index: 50;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 4px;
  color: var(--gray-400);
  font-size: 11px;
  text-decoration: none;
  transition: color .15s;
  gap: 2px;
}

.tab-icon {
  font-size: 20px;
}

.tab-active {
  color: var(--primary);
}
</style>
