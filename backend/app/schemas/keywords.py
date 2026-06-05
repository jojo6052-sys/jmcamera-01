from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SearchKeywordBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    keyword: str
    category: str | None = None
    brand: str | None = None
    model_group: str | None = None
    priority: int = 100
    active: bool = True


class SearchKeywordCreate(SearchKeywordBase):
    pass


class SearchKeywordUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    keyword: str | None = None
    category: str | None = None
    brand: str | None = None
    model_group: str | None = None
    priority: int | None = None
    active: bool | None = None


class SearchKeywordRead(SearchKeywordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
