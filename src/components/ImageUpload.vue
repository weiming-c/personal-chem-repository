<template>
  <div class="image-upload">
    <div v-if="!imageUrl" class="upload-placeholder" @click="triggerUpload">
      <span class="upload-icon">📷</span>
      <p>点击上传题图</p>
      <p class="form-hint">支持 jpg / png</p>
    </div>
    <div v-else class="upload-preview">
      <img :src="imageUrl" alt="预览" class="preview-img" />
      <div class="preview-actions">
        <button class="btn btn-sm btn-outline" @click="triggerUpload">重新上传</button>
        <button class="btn btn-sm btn-ghost" @click="handleRemove">移除</button>
      </div>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png"
      style="display:none"
      @change="handleFileChange"
    />
    <p v-if="uploading" class="upload-status">上传中...</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { uploadImage } from '@/api'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const toast = useToast()
const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const imageUrl = ref(props.modelValue)

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  if (file.size > 10 * 1024 * 1024) {
    toast.show('图片大小不能超过 10MB')
    return
  }

  uploading.value = true
  try {
    const { url } = await uploadImage(file)
    imageUrl.value = url
    emit('update:modelValue', url)
  } catch {
    toast.show('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

function handleRemove() {
  imageUrl.value = ''
  emit('update:modelValue', '')
  if (fileInput.value) fileInput.value.value = ''
}
</script>

<style scoped>
.image-upload {
  width: 100%;
}

.upload-placeholder {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius);
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color .15s;
  color: var(--gray-500);
}

.upload-placeholder:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.upload-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.upload-preview {
  position: relative;
}

.preview-img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: var(--radius);
  background: var(--gray-100);
}

.preview-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: center;
}

.upload-status {
  text-align: center;
  color: var(--gray-500);
  font-size: 13px;
  margin-top: 8px;
}
</style>
