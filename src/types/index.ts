// ==================== 基础数据类型 ====================

// 统一响应结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页参数
export interface PaginationParams {
  page: number
  pageSize: number
}

// 分页响应
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// ==================== 题目相关 ====================

export interface Question {
  id: number
  userId?: number
  content: string        // 题干文本
  answer: string          // 答案文本
  imageUrl: string        // 题图路径（增强后）
  rawImageUrl?: string | null  // 题图原图备份路径
  answerImageUrl: string  // 答案图路径
  remark: string          // 备注
  source: 'private' | 'public'  // 来源
  systemTags: SystemTag[]
  userTags: UserTag[]
  createdAt: string
  updatedAt: string
}

export interface CreateQuestionData {
  content: string
  answer: string
  imageUrl: string
  rawImageUrl?: string | null
  answerImageUrl: string
  remark?: string
  systemTagIds: number[]
  userTagIds: number[]
}

export interface UpdateQuestionData {
  content?: string
  answer?: string
  imageUrl?: string
  rawImageUrl?: string | null
  answerImageUrl?: string
  remark?: string
  systemTagIds?: number[]
  userTagIds?: number[]
}

// ==================== 图片上传 ====================

// 四角归一化坐标（0~1），顺序：[左上, 右上, 右下, 左下]
export interface ImageCorner {
  x: number
  y: number
}

// 图片上传结果
export interface UploadResult {
  url: string                    // 最终图片URL（增强后或原图）
  rawImageUrl?: string | null    // 原图备份URL
  enhanced?: boolean             // 是否执行了增强流水线
}

// ==================== 标签相关 ====================

export interface SystemTag {
  id: number
  name: string
  parentId: number | null
  level: number
  children?: SystemTag[]
  order: number
}

export interface UserTag {
  id: number
  name: string
  userId?: number
  questionCount?: number
  createdAt: string
}

// ==================== 错题相关 ====================

export interface WrongQuestion {
  id: number
  userId?: number
  questionId: number
  question?: Question
  wrongCount: number
  status: WrongQuestionStatus
  note: string
  wrongReason: string
  lastWrongAt: string
  nextReviewAt: string | null
  createdAt: string
  updatedAt: string
}

export type WrongQuestionStatus = 'active' | 'mastered' | 'removed'

export interface UpdateWrongQuestionData {
  status?: WrongQuestionStatus
  note?: string
  wrongReason?: string
}

// ==================== 组卷相关 ====================

export interface Paper {
  id: number
  userId?: number
  name: string
  description: string
  sourceMode: 'private' | 'public' | 'mixed'
  questionIds: number[]
  questions?: Question[]
  questionOrder: number[]  // 自定义排序
  createdAt: string
  updatedAt: string
}

export interface CreatePaperData {
  name: string
  description?: string
  sourceMode: 'private' | 'public' | 'mixed'
  questionIds: number[]
  questionOrder?: number[]
}

export interface PaperFilterParams {
  systemTagIds?: number[]
  userTagIds?: number[]
  wrongQuestionOnly?: boolean
  wrongStatus?: WrongQuestionStatus
  sourceMode?: 'private' | 'public' | 'mixed'
  count?: number
  random?: boolean
}

// ==================== 检索相关 ====================

export interface SearchParams extends PaginationParams {
  keyword: string
  searchScope: 'content' | 'content_answer'  // 仅题干 / 题干+答案
  searchRange: 'private' | 'public' | 'all'
  systemTagIds?: number[]
  userTagIds?: number[]
}

// ==================== 错题筛选 ====================

export interface WrongQuestionFilterParams extends PaginationParams {
  systemTagIds?: number[]
  userTagIds?: number[]
  wrongCountMin?: number
  wrongCountMax?: number
  status?: WrongQuestionStatus
  lastWrongBefore?: string
  lastWrongAfter?: string
}

// ==================== OCR相关 ====================

export interface OcrResult {
  content: string
  answer: string
  confidence: number
}

// ==================== AI相关 ====================

export interface AiTranslateResult {
  originalKeywords: string
  translatedKeywords: string
  suggestion: string
}
