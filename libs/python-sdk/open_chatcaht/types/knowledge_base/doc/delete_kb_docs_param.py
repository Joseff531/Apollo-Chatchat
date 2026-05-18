from typing import List

from pydantic import BaseModel, Field


class DeleteKbDocsParam(BaseModel):
    knowledge_base_name: str = Field(..., examples=["samples"]),
    file_names: List[str] = Field(..., examples=[["file_name.md", "test.txt"]]),
    delete_content: bool = Field(False),
    not_refresh_vs_cache: bool = Field(False, description="Skip persisting the vector store for now (used for FAISS)"),
