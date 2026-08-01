from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "化学竞赛题库"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "a20100105z"
    DB_NAME: str = "chem_question_bank"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # 文件上传
    UPLOAD_DIR: str = str(Path(__file__).parent.parent / "uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # 图片增强（前端框四角 + 后端透视矫正 + 压缩后处理）
    IMAGE_ENHANCE_ENABLED: bool = True
    ENHANCED_MAX_EDGE: int = 1600  # 增强后图片长边像素
    ENHANCED_JPEG_QUALITY: int = 82  # 增强图 JPEG 质量
    KEEP_RAW_IMAGE: bool = True  # 是否保留原图备份（raw_image_url）

    # 当前单用户阶段，硬编码 user_id
    DEFAULT_USER_ID: int = 1

    # OCR 服务
    OCR_ENABLED: bool = False
    OCR_SERVICE_URL: str = "http://localhost:8001"

    # AI 术语映射
    AI_TERM_MAP_PATH: str = str(Path(__file__).parent / "data" / "term_map.json")

    # AI LLM（可选）
    AI_API_URL: str = ""
    AI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
