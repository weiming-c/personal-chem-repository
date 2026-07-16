<template>
  <div class="question-card card" @click="$emit('click')">
    <!-- 题图缩略图 -->
    <img
      v-if="question.imageUrl"
      :src="question.imageUrl"
      class="card-image"
      alt="题图"
    />
    <!-- 题干 -->
    <p class="card-content">{{ truncate(question.content, 120) }}</p>
    <!-- 答案（仅浏览模式显示） -->
    <div v-if="showAnswer && question.answer" class="card-answer">
      <span class="answer-label">答案：</span>{{ question.answer }}
    </div>
    <!-- 标签 -->
    <div class="card-tags" v-if="hasTags">
      <span
        v-for="t in question.systemTags?.slice(0, 3)"
        :key="'s-' + t.id"
        class="tag tag-system"
      >{{ t.name }}</span>
      <span
        v-for="t in question.userTags?.slice(0, 3)"
        :key="'u-' + t.id"
        class="tag tag-user"
      >{{ t.name }}</span>
      <span v-if="moreTags > 0" class="tag" style="background:var(--gray-100);color:var(--gray-500)">
        +{{ moreTags }}
      </span>
    </div>
    <!-- 来源标识 & 时间 -->
    <div class="card-meta">
      <span v-if="question.source === 'public'" class="tag tag-public">公共题</span>
      <span v-else class="tag" style="background:var(--gray-100);color:var(--gray-500)">私有</span>
      <span class="card-time">{{ formatTime(question.createdAt) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Question } from '@/types'

const props = withDefaults(defineProps<{
  question: Question
  showAnswer?: boolean
}>(), {
  showAnswer: false,
})

defineEmits<{
  click: []
}>()

const hasTags = computed(() => {
  return (props.question.systemTags?.length || 0) + (props.question.userTags?.length || 0) > 0
})

const moreTags = computed(() => {
  const s = props.question.systemTags?.length || 0
  const u = props.question.userTags?.length || 0
  return Math.max(0, s - 3) + Math.max(0, u - 3)
})

function truncate(text: string, len: number) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<style scoped>
.question-card {
  cursor: pointer;
  transition: box-shadow .15s;
}

.question-card:hover {
  box-shadow: var(--shadow-md);
}

.card-image {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  margin-bottom: 10px;
  background: var(--gray-100);
}

.card-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--gray-800);
  word-break: break-word;
}

.card-answer {
  margin-top: 10px;
  padding: 10px;
  background: var(--success-bg);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--success);
  line-height: 1.6;
}

.answer-label {
  font-weight: 600;
}

.card-tags {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.card-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-time {
  font-size: 12px;
  color: var(--gray-400);
  margin-left: auto;
}
</style>
