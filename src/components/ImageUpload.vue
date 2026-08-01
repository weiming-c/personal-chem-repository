<template>
  <div ref="containerEl" class="image-upload">
    <!-- 空态：选择文件 -->
    <div v-if="state === 'idle'" class="upload-placeholder" @click="triggerUpload">
      <span class="upload-icon">📷</span>
      <p>点击上传题图</p>
      <p class="form-hint">支持 jpg / png / webp</p>
    </div>

    <!-- 矫正态：画布框四角 -->
    <div v-else-if="state === 'adjust'" class="adjust-panel">
      <div class="adjust-canvas-wrap">
        <canvas
          ref="canvasEl"
          class="adjust-canvas"
          :width="canvasW"
          :height="canvasH"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
        />
      </div>
      <p class="form-hint">拖动四个角点框住题目区域，可矫正拍摄角度</p>
      <div class="adjust-actions">
        <button class="btn btn-primary" :disabled="uploading" @click="confirmUpload">
          {{ uploading ? '上传中...' : '确认上传' }}
        </button>
        <button class="btn btn-outline" :disabled="uploading" @click="skipUpload">
          跳过矫正
        </button>
      </div>
    </div>

    <!-- 预览态：已上传 -->
    <div v-else class="upload-preview">
      <img :src="displayUrl" alt="预览" class="preview-img" />
      <div v-if="rawImageUrl" class="raw-toggle">
        <label>
          <input type="checkbox" v-model="showRaw" /> 查看原图
        </label>
      </div>
      <div class="preview-actions">
        <button class="btn btn-sm btn-outline" @click="startAdjust">重新上传</button>
        <button class="btn btn-sm btn-ghost" @click="handleRemove">移除</button>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      style="display:none"
      @change="handleFileChange"
    />
    <p v-if="uploading && state === 'preview'" class="upload-status">上传中...</p>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { uploadImage } from '@/api'
import { useToast } from '@/composables/useToast'
import type { ImageCorner } from '@/types'

const props = defineProps<{
  modelValue: string
  rawImageUrl?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:rawImageUrl': [value: string | null]
}>()

const toast = useToast()

type UiState = 'idle' | 'adjust' | 'preview'

const state = ref<UiState>(props.modelValue ? 'preview' : 'idle')
const fileInput = ref<HTMLInputElement>()
const containerEl = ref<HTMLDivElement>()
const canvasEl = ref<HTMLCanvasElement>()
const uploading = ref(false)
const showRaw = ref(false)
const rawImageUrl = ref<string | null>(props.rawImageUrl ?? null)

// ---- 画布矫正状态 ----
const imgElement = ref<HTMLImageElement | null>(null)
const canvasW = ref(0)
const canvasH = ref(0)
const corners = ref<ImageCorner[]>([])
let dragIndex = -1
let resizeObserver: ResizeObserver | null = null

const displayUrl = computed(() =>
  showRaw.value && rawImageUrl.value ? rawImageUrl.value : props.modelValue
)

watch(
  () => props.modelValue,
  (val) => {
    // 外部清空时回到空态；外部赋新值时切到预览
    if (!val) state.value = 'idle'
    else if (state.value === 'adjust') state.value = 'preview'
  }
)

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  if (file.size > 10 * 1024 * 1024) {
    toast.show('图片大小不能超过 10MB')
    return
  }

  loadToCanvas(file)
}

/** 将选中图片加载到画布，进入框四角模式 */
function loadToCanvas(file: File) {
  const url = URL.createObjectURL(file)
  const img = new Image()
  img.onload = () => {
    imgElement.value = img
    corners.value = []
    state.value = 'adjust'
    // canvas 由 v-if 挂载，需等 DOM 更新后再绘制
    nextTick(() => fitCanvas(true))
    URL.revokeObjectURL(url)
  }
  img.onerror = () => {
    toast.show('图片加载失败')
    URL.revokeObjectURL(url)
  }
  img.src = url
}

/** 计算画布显示尺寸（等比缩放，宽度优先），并初始化默认贴角 */
function fitCanvas(initCorners = false) {
  const img = imgElement.value
  if (!img) return
  const wrapW = containerEl.value?.clientWidth || 420
  const maxH = 340
  let w = wrapW
  let h = w * (img.naturalHeight / img.naturalWidth)
  if (h > maxH) {
    h = maxH
    w = h * (img.naturalWidth / img.naturalHeight)
  }
  canvasW.value = Math.max(1, Math.round(w))
  canvasH.value = Math.max(1, Math.round(h))
  if (initCorners || corners.value.length !== 4) {
    // 默认贴住图片四角
    corners.value = [
      { x: 0, y: 0 },
      { x: canvasW.value, y: 0 },
      { x: canvasW.value, y: canvasH.value },
      { x: 0, y: canvasH.value },
    ]
  }
  draw()
}

function draw() {
  const canvas = canvasEl.value
  const img = imgElement.value
  if (!canvas || !img) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, canvasW.value, canvasH.value)
  ctx.drawImage(img, 0, 0, canvasW.value, canvasH.value)

  // 四边形区域外蒙版变暗（evenodd：先画全矩形，再画四边形）
  ctx.beginPath()
  ctx.rect(0, 0, canvasW.value, canvasH.value)
  ctx.moveTo(corners.value[0].x, corners.value[0].y)
  for (let i = 1; i < 4; i++) {
    ctx.lineTo(corners.value[i].x, corners.value[i].y)
  }
  ctx.closePath()
  ctx.fillStyle = 'rgba(0,0,0,0.45)'
  ctx.fill('evenodd')

  // 绿色边框
  ctx.beginPath()
  ctx.moveTo(corners.value[0].x, corners.value[0].y)
  for (let i = 1; i < 4; i++) {
    ctx.lineTo(corners.value[i].x, corners.value[i].y)
  }
  ctx.closePath()
  ctx.strokeStyle = '#16a34a'
  ctx.lineWidth = 2.5
  ctx.stroke()

  // 四角手柄
  for (const c of corners.value) {
    ctx.beginPath()
    ctx.arc(c.x, c.y, 8, 0, Math.PI * 2)
    ctx.fillStyle = '#16a34a'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
  }
}

function onPointerDown(e: PointerEvent) {
  const { x, y } = toCanvasPos(e)
  dragIndex = corners.value.findIndex((c) => Math.hypot(c.x - x, c.y - y) < 16)
  if (dragIndex >= 0) {
    canvasEl.value?.setPointerCapture(e.pointerId)
    updateCorner(x, y)
  }
}

function onPointerMove(e: PointerEvent) {
  if (dragIndex < 0) return
  const { x, y } = toCanvasPos(e)
  updateCorner(x, y)
}

function onPointerUp() {
  dragIndex = -1
}

function toCanvasPos(e: PointerEvent) {
  const rect = canvasEl.value!.getBoundingClientRect()
  const scaleX = canvasW.value / rect.width
  const scaleY = canvasH.value / rect.height
  return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY }
}

function updateCorner(x: number, y: number) {
  const clamped = {
    x: Math.max(0, Math.min(canvasW.value, x)),
    y: Math.max(0, Math.min(canvasH.value, y)),
  }
  corners.value[dragIndex] = clamped
  draw()
}

/** 四角像素坐标 → 0~1 归一化坐标 */
function normalizeCorners(): ImageCorner[] {
  return corners.value.map((c) => ({
    x: Math.min(1, Math.max(0, c.x / canvasW.value)),
    y: Math.min(1, Math.max(0, c.y / canvasH.value)),
  }))
}

async function confirmUpload() {
  const file = fileInput.value?.files?.[0]
  if (!file) return
  await doUpload(file, normalizeCorners())
}

async function skipUpload() {
  const file = fileInput.value?.files?.[0]
  if (!file) return
  await doUpload(file)
}

async function doUpload(file: File, corners?: ImageCorner[]) {
  uploading.value = true
  try {
    const res = await uploadImage(file, corners)
    rawImageUrl.value = res.rawImageUrl ?? null
    showRaw.value = false
    state.value = 'preview'
    emit('update:modelValue', res.url)
    emit('update:rawImageUrl', rawImageUrl.value)
  } catch {
    toast.show('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

function startAdjust() {
  // 重新选择文件，保留旧值直到成功
  fileInput.value!.value = ''
  triggerUpload()
}

function handleRemove() {
  rawImageUrl.value = null
  showRaw.value = false
  emit('update:modelValue', '')
  emit('update:rawImageUrl', null)
  if (fileInput.value) fileInput.value.value = ''
  state.value = 'idle'
}

// 容器尺寸变化时重绘
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})

watch(
  () => containerEl.value,
  (el) => {
    resizeObserver?.disconnect()
    if (el && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        if (state.value === 'adjust') fitCanvas(false)
      })
      resizeObserver.observe(el)
    }
  }
)
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

.adjust-panel {
  width: 100%;
}

.adjust-canvas-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}

.adjust-canvas {
  max-width: 100%;
  border-radius: var(--radius);
  background: var(--gray-100);
  cursor: grab;
  touch-action: none;
}

.adjust-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: center;
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

.raw-toggle {
  margin-top: 6px;
  text-align: center;
  font-size: 13px;
  color: var(--gray-500);
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
