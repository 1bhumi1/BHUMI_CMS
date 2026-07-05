from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str = "An error occurred"
    errors: list[Any] = []
