from typing import Optional

from pydantic import BaseModel, Field
from datetime import datetime


class KnowledgeBaseInfo(BaseModel):
    id: int = Field(default=None,  description="Knowledge base ID")
    kb_name: str = Field(default=None,  description="Knowledge base name")
    kb_info: Optional[str] = Field(default=None,  description="Knowledge base information")
    vs_type: Optional[str] = Field(default=None,  description="Vector store type")
    embed_model: Optional[str] = Field(default=None,  description="Embedding model")
    file_count: Optional[int] = Field(default=None,  description="File count")
    create_time: Optional[datetime] = Field(default=None,  description="Creation time")
