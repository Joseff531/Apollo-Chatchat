from typing import Optional

from pydantic import Field, BaseModel


class CreateKnowledgeBaseParam(BaseModel):
    knowledge_base_name: str = Field(default=None, description="Knowledge base name")
    vector_store_type: str = Field(default=None, description="Vector store type")
    kb_info: Optional[str] = Field(default=None, description="Knowledge base information")
    vs_type: Optional[str] = Field(default=None, description="Vector store type")
    embed_model: Optional[str] = Field(default=None, description="Embedding model")
