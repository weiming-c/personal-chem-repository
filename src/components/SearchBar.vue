<template>
  <div class="search-bar-wrapper">
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input
        ref="inputRef"
        v-model="keyword"
        class="search-input"
        :placeholder="placeholder"
        @keyup.enter="handleSearch"
        @input="handleInput"
      />
      <button v-if="keyword" class="search-clear" @click="clearSearch">×</button>
      <button v-if="showAiButton" class="btn btn-sm btn-ghost ai-btn" @click="$emit('aiSearch')" title="AI 智能搜索">
        ✨
      </button>
    </div>
    <!-- 搜索范围选项 -->
    <div class="search-options" v-if="showOptions">
      <div class="option-row">
        <label class="radio-label">
          <input type="radio" value="content" v-model="searchScope" />
          仅题干
        </label>
        <label class="radio-label">
          <input type="radio" value="content_answer" v-model="searchScope" />
          题干+答案
        </label>
      </div>
      <div class="option-row">
        <label class="radio-label">
          <input type="radio" value="private" v-model="searchRange" />
          仅私有库
        </label>
        <label class="radio-label">
          <input type="radio" value="all" v-model="searchRange" />
          包含公共库
        </label>
      </div>
    </div>
    <!-- 按钮 -->
    <button v-if="showSearchBtn" class="btn btn-primary btn-block" @click="handleSearch">
      搜索
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  placeholder?: string
  showOptions?: boolean
  showAiButton?: boolean
  showSearchBtn?: boolean
  modelValue?: string
}>(), {
  placeholder: '搜索题目...',
  showOptions: true,
  showAiButton: true,
  showSearchBtn: false,
  modelValue: '',
})

const emit = defineEmits<{
  search: [params: { keyword: string; searchScope: string; searchRange: string }]
  aiSearch: []
  'update:modelValue': [value: string]
}>()

const keyword = ref(props.modelValue)
const searchScope = ref<'content' | 'content_answer'>('content_answer')
const searchRange = ref<'private' | 'all'>('all')
const inputRef = ref<HTMLInputElement>()

watch(() => props.modelValue, (v) => {
  keyword.value = v
})

function handleSearch() {
  emit('search', {
    keyword: keyword.value,
    searchScope: searchScope.value,
    searchRange: searchRange.value,
  })
}

function handleInput() {
  emit('update:modelValue', keyword.value)
}

function clearSearch() {
  keyword.value = ''
  emit('update:modelValue', '')
}

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.search-bar-wrapper {
  padding: 0 20px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--gray-50);
  border-radius: 24px;
  padding: 10px 16px;
  border: 1.5px solid transparent;
  transition: border-color .15s, box-shadow .15s;
}

.search-bar:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, .1);
  background: #fff;
}

.search-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: var(--gray-800);
  min-width: 0;
}

.search-input::placeholder {
  color: var(--gray-400);
}

.search-clear {
  border: none;
  background: var(--gray-300);
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-btn {
  flex-shrink: 0;
  font-size: 16px;
}

.search-options {
  margin-top: 10px;
}

.option-row {
  display: flex;
  gap: 20px;
  margin-bottom: 6px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--gray-600);
  cursor: pointer;
}

.radio-label input {
  accent-color: var(--primary);
}
</style>
