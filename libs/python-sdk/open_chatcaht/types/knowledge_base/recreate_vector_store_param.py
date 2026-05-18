
from pydantic import BaseModel, Field

from open_chatcaht._constants import VS_TYPE, EMBEDDING_MODEL, CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE


class RecreateVectorStoreParam(BaseModel):
    knowledge_base_name: str = Field(..., examples=["samples"], description='Knowledge base name'),
    allow_empty_kb: bool = Field(True),
    vs_type: str = Field(VS_TYPE, description='Vector store type'),
    embed_model: str = Field(EMBEDDING_MODEL, description="Embedding model"),
    chunk_size: int = Field(CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
    chunk_overlap: int = Field(OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
    zh_title_enhance: bool = Field(ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
    not_refresh_vs_cache: bool = Field(False, description="Skip persisting the vector store for now (used for FAISS)")
