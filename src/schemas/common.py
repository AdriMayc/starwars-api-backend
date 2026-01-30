# src/schemas/common.py
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ErrorItem(BaseModel):
    code: str = Field(..., examples=["VALIDATION_ERROR", "NOT_FOUND", "UPSTREAM_TIMEOUT"])
    message: str = Field(..., examples=["Invalid query parameter", "Resource not found"])
    details: Optional[dict[str, Any]] = Field(default=None)


class Meta(BaseModel):
    request_id: str = Field(..., examples=["c2f0f6a0-2f2d-4dc5-9f1f-0a7b0b7f2a33"])
    page: Optional[int] = None
    page_size: Optional[int] = None
    count: Optional[int] = None
    total: Optional[int] = None


class Links(BaseModel):
    self: str
    next: Optional[str] = None
    prev: Optional[str] = None


class Envelope(BaseModel, Generic[T]):
    """
    Envelope padrão da API: sempre o mesmo shape.

    data: payload principal (pode ser dict, list, objeto)
    meta: metadados (request_id obrigatório)
    links: self/next/prev (self obrigatório)
    errors: lista de erros (vazia no sucesso)
    """
    model_config = ConfigDict(extra="forbid")

    data: Optional[T] = None
    meta: Meta
    links: Links
    errors: list[ErrorItem] = Field(default_factory=list)


def ok(*, data: T, request_id: str, self_url: str, meta: Optional[dict[str, Any]] = None,
       next_url: Optional[str] = None, prev_url: Optional[str] = None) -> Envelope[T]:
    meta_obj = Meta(request_id=request_id, **(meta or {}))
    links_obj = Links(self=self_url, next=next_url, prev=prev_url)
    return Envelope[T](data=data, meta=meta_obj, links=links_obj, errors=[])


def fail(*, request_id: str, self_url: str, status_code: int,
         errors: list[ErrorItem], meta: Optional[dict[str, Any]] = None) -> tuple[int, Envelope[None]]:
    """
    Retorna (status_code, envelope) para simplificar handlers.
    """
    meta_obj = Meta(request_id=request_id, **(meta or {}))
    links_obj = Links(self=self_url)
    env = Envelope[None](data=None, meta=meta_obj, links=links_obj, errors=errors)
    return status_code, env
