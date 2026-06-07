from pydantic import BaseModel


class ProductImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
