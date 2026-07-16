-- ============================================
-- 化学竞赛题库 - 数据库初始化 DDL
-- PostgreSQL
-- ============================================

-- 创建数据库（需在 psql 中手动执行）
-- CREATE DATABASE chem_question_bank;

-- 题目表
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    image_url VARCHAR(500),
    content TEXT NOT NULL,
    answer TEXT,
    note TEXT,
    source VARCHAR(20) NOT NULL DEFAULT 'private',
    search_vector TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_questions_user_id ON questions(user_id);
CREATE INDEX idx_questions_source ON questions(source);
CREATE INDEX idx_questions_is_deleted ON questions(is_deleted);

-- 系统预设标签表（树形结构）
CREATE TABLE IF NOT EXISTS system_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES system_tags(id),
    level INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_system_tags_parent ON system_tags(parent_id);

-- 用户自定义标签表（扁平结构）
CREATE TABLE IF NOT EXISTS user_tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_tags_user_id ON user_tags(user_id);
CREATE UNIQUE INDEX idx_user_tags_name_user ON user_tags(user_id, name);

-- 题目-标签关联表
CREATE TABLE IF NOT EXISTS question_tags (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    system_tag_id INTEGER REFERENCES system_tags(id) ON DELETE CASCADE,
    user_tag_id INTEGER REFERENCES user_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_question_tags_question ON question_tags(question_id);
CREATE INDEX idx_question_tags_system ON question_tags(system_tag_id);
CREATE INDEX idx_question_tags_user ON question_tags(user_tag_id);

-- 错题记录表
CREATE TABLE IF NOT EXISTS wrong_questions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    error_count INTEGER DEFAULT 1,
    note TEXT,
    status VARCHAR(20) DEFAULT 'active',
    last_review_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wrong_questions_user ON wrong_questions(user_id);
CREATE INDEX idx_wrong_questions_question ON wrong_questions(question_id);
CREATE INDEX idx_wrong_questions_status ON wrong_questions(status);

-- 确保同一用户同一题只有一条活跃错题记录
CREATE UNIQUE INDEX idx_wrong_questions_unique_active
    ON wrong_questions(user_id, question_id)
    WHERE status = 'active';

-- 试卷表
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1,
    title VARCHAR(200) NOT NULL,
    source_filter VARCHAR(20),
    conditions TEXT,
    question_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_papers_user_id ON papers(user_id);

-- 试卷-题目关联表
CREATE TABLE IF NOT EXISTS paper_questions (
    id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_paper_questions_paper ON paper_questions(paper_id);

-- 全文检索支持（pg_bigm 三文字组索引，可选）
-- CREATE EXTENSION IF NOT EXISTS pg_bigm;
-- CREATE INDEX idx_questions_content_bigm ON questions USING gin (content gin_bigm_ops);

-- 简易全文检索（使用 ILIKE + tsvector）
-- 为 content 和 answer 字段创建 tsvector 列
ALTER TABLE questions ADD COLUMN IF NOT EXISTS content_tsv tsvector;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS answer_tsv tsvector;

-- 创建 tsvector 触发器函数
CREATE OR REPLACE FUNCTION questions_tsv_trigger() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('simple', COALESCE(NEW.content, ''));
    IF NEW.answer IS NOT NULL THEN
        NEW.answer_tsv := to_tsvector('simple', NEW.answer);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 删除旧触发器（如果存在）后重建
DROP TRIGGER IF EXISTS trg_questions_tsv ON questions;
CREATE TRIGGER trg_questions_tsv
    BEFORE INSERT OR UPDATE OF content, answer ON questions
    FOR EACH ROW EXECUTE FUNCTION questions_tsv_trigger();

-- 创建 GIN 索引加速全文检索
CREATE INDEX IF NOT EXISTS idx_questions_content_tsv ON questions USING gin(content_tsv);
CREATE INDEX IF NOT EXISTS idx_questions_answer_tsv ON questions USING gin(answer_tsv);
