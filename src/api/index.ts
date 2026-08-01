import axios from 'axios'
import type {
  ApiResponse,
  PaginatedData,
  Question,
  CreateQuestionData,
  UpdateQuestionData,
  SystemTag,
  UserTag,
  WrongQuestion,
  WrongQuestionFilterParams,
  UpdateWrongQuestionData,
  Paper,
  CreatePaperData,
  PaperFilterParams,
  SearchParams,
  OcrResult,
  AiTranslateResult,
  ImageCorner,
  UploadResult,
} from '@/types'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器
http.interceptors.response.use(
  (res) => {
    const body = res.data as ApiResponse
    if (body.code !== 0) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return res
  },
  (err) => Promise.reject(err)
)

function unwrap<T>(res: any): T {
  return (res.data as ApiResponse<T>).data
}

// ==================== 题目 ====================

export function createQuestion(data: CreateQuestionData) {
  const formData = new FormData()
  formData.append('content', data.content)
  formData.append('answer', data.answer || '')
  if (data.imageUrl) formData.append('image_url', data.imageUrl)
  if (data.rawImageUrl) formData.append('raw_image_url', data.rawImageUrl)
  if (data.answerImageUrl) formData.append('answer_image_url', data.answerImageUrl)
  if (data.remark) formData.append('note', data.remark)
  formData.append('system_tag_ids', data.systemTagIds.join(','))
  formData.append('user_tag_ids', data.userTagIds.join(','))
  return http.post('/questions', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((res) => unwrap<Question>(res))
}

export function getQuestions(params: { page: number; pageSize: number; system_tag_ids?: string; user_tag_ids?: string; source?: string; keyword?: string }) {
  return http.get('/questions', { params }).then((res) => unwrap<PaginatedData<Question>>(res))
}

export function getQuestion(id: number) {
  return http.get(`/questions/${id}`).then((res) => unwrap<Question>(res))
}

export function updateQuestion(id: number, data: UpdateQuestionData) {
  return http.put(`/questions/${id}`, data).then((res) => unwrap<Question>(res))
}

export function deleteQuestion(id: number) {
  return http.delete(`/questions/${id}`).then((res) => unwrap<null>(res))
}

// ==================== 标签 ====================

export function getSystemTags() {
  return http.get('/tags/system').then((res) => unwrap<SystemTag[]>(res))
}

export function getUserTags() {
  return http.get('/tags/user').then((res) => unwrap<UserTag[]>(res))
}

export function createUserTag(name: string) {
  return http.post('/tags/user', { name }).then((res) => unwrap<UserTag>(res))
}

export function deleteUserTag(id: number) {
  return http.delete(`/tags/user/${id}`).then((res) => unwrap<null>(res))
}

export function batchTagQuestions(data: { questionIds: number[]; userTagIds: number[]; action: 'add' | 'remove' }) {
  return http.post('/questions/batch-tag', data).then((res) => unwrap<null>(res))
}

// ==================== 检索 ====================

export function searchQuestions(params: SearchParams) {
  const q: Record<string, any> = {
    keyword: params.keyword,
    search_scope: params.searchScope,
    search_range: params.searchRange,
    page: params.page,
    pageSize: params.pageSize,
  }
  if (params.systemTagIds && params.systemTagIds.length > 0) {
    q.system_tag_ids = params.systemTagIds.join(',')
  }
  return http.get('/search', { params: q }).then((res) => unwrap<PaginatedData<Question>>(res))
}

// ==================== 错题 ====================

export function getWrongQuestions(params: WrongQuestionFilterParams) {
  return http.get('/wrong-questions', { params }).then((res) => unwrap<PaginatedData<WrongQuestion>>(res))
}

export function markWrongQuestion(questionId: number) {
  return http.post('/wrong-questions', { questionId }).then((res) => unwrap<WrongQuestion>(res))
}

export function updateWrongQuestion(id: number, data: UpdateWrongQuestionData) {
  return http.put(`/wrong-questions/${id}`, data).then((res) => unwrap<WrongQuestion>(res))
}

export function removeWrongQuestion(id: number) {
  return http.delete(`/wrong-questions/${id}`).then((res) => unwrap<null>(res))
}

// ==================== 组卷 ====================

export function createPaper(data: CreatePaperData) {
  return http.post('/papers', data).then((res) => unwrap<Paper>(res))
}

export function getPapers(params?: { page?: number; pageSize?: number }) {
  return http.get('/papers', { params }).then((res) => unwrap<PaginatedData<Paper>>(res))
}

export function getPaper(id: number) {
  return http.get(`/papers/${id}`).then((res) => unwrap<Paper>(res))
}

export function deletePaper(id: number) {
  return http.delete(`/papers/${id}`).then((res) => unwrap<null>(res))
}

// ==================== OCR ====================

export function ocrRecognize(imageUrl: string, imageType: 'question' | 'answer' = 'question') {
  return http.post('/ocr/recognize', { imageUrl, imageType }, { timeout: 120000 }).then((res) => unwrap<OcrResult>(res))
}

// ==================== AI ====================

export function aiTranslate(keywords: string) {
  return http.post('/ai/translate', { keywords }).then((res) => unwrap<AiTranslateResult>(res))
}

// ==================== 图片上传 ====================

/**
 * 上传图片，可选携带四角归一化坐标触发后端透视矫正增强
 *
 * @param file    图片文件
 * @param corners 四角坐标 [{x,y}*4]，顺序[左上,右上,右下,左下]；缺省/不足4点时后端直接存原图
 */
export function uploadImage(file: File, corners?: ImageCorner[]) {
  const formData = new FormData()
  formData.append('file', file)
  if (corners && corners.length === 4) {
    formData.append('corners', JSON.stringify(corners))
  }
  return http.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000, // 增强流水线耗时较长，放宽超时
  }).then((res) => unwrap<UploadResult>(res))
}
