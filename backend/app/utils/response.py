from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Any = None


class PaginatedResponse(ApiResponse):
    total: int = 0
    page: int = 1
    page_size: int = 20


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def paginated(
    data: Any,
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    return {
        "code": 0,
        "message": "success",
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def error(code: int = -1, message: str = "error", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
