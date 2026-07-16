<template>
  <div class="question-edit-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>{{ isEdit ? '编辑题目' : '录入题目' }}</h1>
    </div>
    <div class="page-body">
      <!-- 题图上传 -->
      <div class="form-group">
        <label class="form-label">题图</label>
        <ImageUpload v-model="imageUrl" />
      </div>

      <!-- OCR 识别按钮（有图片时显示） -->
      <div v-if="imageUrl" class="ocr-section">
        <button class="btn btn-outline btn-block" :disabled="ocrLoading" @click="handleOcr">
          {{ ocrLoading ? '识别中...' : '🔍 OCR 识别' }}
        </button>
        <p v-if="ocrResult" class="ocr-hint">
          识别置信度：{{ (ocrResult.confidence * 100).toFixed(0) }}%
        </p>
      </div>

      <!-- 题干 -->
      <div class="form-group">
        <label class="form-label">题干</label>
        <textarea
          v-model="content"
          class="form-textarea"
          rows="4"
          placeholder="输入题干或使用 OCR 识别..."
        ></textarea>
      </div>

      <!-- 答案 -->
      <div class="form-group">
        <label class="form-label">答案（可选）</label>
        <textarea
          v-model="answer"
          class="form-textarea"
          rows="3"
          placeholder="输入答案..."
        ></textarea>
      </div>

      <!-- 标签选择 -->
      <div class="form-group">
        <label class="form-label">标签</label>
        <TagSelector
          v-model:modelSystemTagIds="systemTagIds"
          v-model:modelUserTagIds="userTagIds"
        />
      </div>

      <!-- 备注 -->
      <div class="form-group">
        <label class="form-label">备注（可选）</label>
        <textarea
          v-model="remark"
          class="form-textarea"
          rows="2"
          placeholder="添加备注信息..."
        ></textarea>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="fixed-bottom">
      <button class="btn btn-primary btn-block" :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '录入题库') }}
      </button>
      <button
        v-if="isEdit"
        class="btn btn-danger btn-block"
        style="margin-top:8px"
        @click="handleDelete"
      >
        删除题目
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ImageUpload from '@/components/ImageUpload.vue'
import TagSelector from '@/components/TagSelector.vue'
import { useQuestionStore } from '@/stores/question'
import { useToast } from '@/composables/useToast'
import { ocrRecognize } from '@/api'
import type { OcrResult } from '@/types'

const route = useRoute()
const router = useRouter()
const questionStore = useQuestionStore()
const toast = useToast()

const isEdit = computed(() => route.name === 'questionEdit')
const questionId = computed(() => Number(route.params.id))

const imageUrl = ref('')
const content = ref('')
const answer = ref('')
const remark = ref('')
const systemTagIds = ref<number[]>([])
const userTagIds = ref<number[]>([])
const ocrLoading = ref(false)
const ocrResult = ref<OcrResult | null>(null)
const submitting = ref(false)

async function handleOcr() {
  ocrLoading.value = true
  try {
    const result = await ocrRecognize(imageUrl.value)
    ocrResult.value = result
    if (result.content && !content.value) {
      content.value = result.content
    }
    if (result.answer) {
      answer.value = result.answer
    }
    toast.show('识别完成')
  } catch {
    toast.show('OCR 识别失败')
  } finally {
    ocrLoading.value = false
  }
}

async function handleSubmit() {
  if (!content.value.trim()) {
    toast.show('请输入题干')
    return
  }
  submitting.value = true
  try {
    const data = {
      content: content.value,
      answer: answer.value,
      imageUrl: imageUrl.value,
      remark: remark.value,
      systemTagIds: systemTagIds.value,
      userTagIds: userTagIds.value,
    }
    if (isEdit.value) {
      await questionStore.editQuestion(questionId.value, data)
      toast.show('修改成功')
    } else {
      await questionStore.addQuestion(data)
      toast.show('录入成功')
    }
    router.back()
  } catch {
    toast.show('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  if (!confirm('确认删除该题目？')) return
  try {
    await questionStore.removeQuestion(questionId.value)
    toast.show('已删除')
    router.replace('/questions')
  } catch {
    toast.show('删除失败')
  }
}

onMounted(async () => {
  if (isEdit.value) {
    const q = await questionStore.fetchQuestion(questionId.value)
    if (q) {
      imageUrl.value = q.imageUrl || ''
      content.value = q.content
      answer.value = q.answer || ''
      remark.value = q.remark || ''
      systemTagIds.value = q.systemTags?.map((t) => t.id) || []
      userTagIds.value = q.userTags?.map((t) => t.id) || []
    }
  }
})
</script>

<style scoped>
.ocr-section {
  margin-bottom: 16px;
}

.ocr-hint {
  text-align: center;
  font-size: 12px;
  color: var(--gray-400);
  margin-top: 6px;
}
</style>
