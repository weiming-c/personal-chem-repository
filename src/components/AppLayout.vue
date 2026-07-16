<template>
  <div class="app-layout">
    <slot />
    <!-- 底部导航栏，除刷题页外均显示 -->
    <TabBar v-if="!hideTabBar" />
    <!-- Toast 消息 -->
    <teleport to="body">
      <Transition name="fade">
        <div v-if="toast.visible" class="toast">{{ toast.message }}</div>
      </Transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TabBar from './TabBar.vue'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const toast = useToast()

// 刷题页不显示底部导航
const hideTabBar = computed(() => {
  return route.name === 'practice'
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}
</style>
