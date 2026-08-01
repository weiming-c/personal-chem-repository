<template>
  <div class="question-edit-page">
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">←</button>
      <h1>{{ isEdit ? '编辑题目' : '录入题目' }}</h1>
    </div>
    <div class="page-body">
      <!-- 题图上传 -->
      <div class="form-group">
        <label class="form-label">题目图片</label>
        <ImageUpload v-model="imageUrl" v-model:rawImageUrl="rawImageUrl" />
        <div v-if="imageUrl" class="ocr-section">
          <button class="btn btn-outline btn-block btn-sm" :disabled="ocrLoadingQ" @click="handleOcrQuestion">
            {{ ocrLoadingQ ? '识别中（约30秒，请耐心等待）...' : '🔍 识别题目图片' }}
          </button>
        </div>
      </div>

      <!-- 答案图上传 -->
      <div class="form-group">
        <label class="form-label">答案图片（可选）</label>
        <ImageUpload v-model="answerImageUrl" />
        <div v-if="answerImageUrl" class="ocr-section">
          <button class="btn btn-outline btn-block btn-sm" :disabled="ocrLoadingA" @click="handleOcrAnswer">
            {{ ocrLoadingA ? '识别中（约30秒，请耐心等待）...' : '🔍 识别答案图片' }}
          </button>
        </div>
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
          placeholder="输入答案或使用 OCR 识别..."
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

const route = useRoute()
const router = useRouter()
const questionStore = useQuestionStore()
const toast = useToast()

const isEdit = computed(() => route.name === 'questionEdit')
const questionId = computed(() => Number(route.params.id))

const imageUrl = ref('')
const rawImageUrl = ref<string | null>(null)
const answerImageUrl = ref('')
const content = ref('')
const answer = ref('')
const remark = ref('')
const systemTagIds = ref<number[]>([])
const userTagIds = ref<number[]>([])
const ocrLoadingQ = ref(false)
const ocrLoadingA = ref(false)
const submitting = ref(false)

async function handleOcrQuestion() {
  ocrLoadingQ.value = true
  try {
    const result = await ocrRecognize(imageUrl.value, 'question')
    content.value = result.content || content.value
    toast.show('题目图片识别完成')
  } catch {
    toast.show('OCR 识别失败，请重试', 4000)
  } finally {
    ocrLoadingQ.value = false
  }
}

async function handleOcrAnswer() {
  ocrLoadingA.value = true
  try {
    const result = await ocrRecognize(answerImageUrl.value, 'answer')
    answer.value = result.content || answer.value
    toast.show('答案图片识别完成')
  } catch {
    toast.show('OCR 识别失败，请重试', 4000)
  } finally {
    ocrLoadingA.value = false
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
      rawImageUrl: rawImageUrl.value,
      answerImageUrl: answerImageUrl.value,
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
      rawImageUrl.value = q.rawImageUrl || null
      answerImageUrl.value = q.answerImageUrl || ''
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
  margin-top: 8px;
}
</style>
