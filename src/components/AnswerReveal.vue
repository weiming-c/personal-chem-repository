<template>
  <div class="answer-reveal">
    <div v-if="!revealed" class="answer-hidden" @click="reveal">
      <span class="lock-icon">🔒</span>
      <span class="reveal-text">点击查看答案</span>
    </div>
    <div v-else class="answer-shown">
      <div class="answer-body" v-html="renderedAnswer"></div>
      <div class="answer-actions">
        <button class="btn btn-sm btn-danger" @click="$emit('markWrong')">
          加入错题本
        </button>
        <button v-if="showMastered" class="btn btn-sm btn-success" @click="$emit('markMastered')">
          已掌握
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  answer: string
  showMastered?: boolean
}>(), {
  showMastered: false,
})

defineEmits<{
  markWrong: []
  markMastered: []
}>()

const revealed = ref(false)
const renderedAnswer = computed(() => {
  return (props.answer || '').replace(/\n/g, '<br/>')
})

function reveal() {
  revealed.value = true
}

// 暴露方法给父组件
defineExpose({ reveal, reset: () => { revealed.value = false } })
</script>

<style scoped>
.answer-hidden {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  background: linear-gradient(135deg, var(--gray-100), #fff);
  border: 1.5px dashed var(--gray-300);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all .2s;
  user-select: none;
}

.answer-hidden:hover {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.answer-hidden:active {
  transform: scale(.98);
}

.lock-icon {
  font-size: 20px;
}

.reveal-text {
  font-size: 15px;
  color: var(--gray-500);
  font-weight: 500;
}

.answer-shown {
  border: 1.5px solid var(--success);
  border-radius: var(--radius);
  overflow: hidden;
}

.answer-body {
  padding: 16px;
  font-size: 15px;
  line-height: 1.8;
  color: var(--gray-800);
  background: var(--success-bg);
}

.answer-actions {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid var(--gray-100);
}
</style>
