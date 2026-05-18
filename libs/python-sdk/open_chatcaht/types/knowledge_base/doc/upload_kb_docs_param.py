from pydantic import BaseModel, Field
from open_chatcaht._constants import CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE


class UploadKbDocsParam(BaseModel):
    knowledge_base_name: str = Field(
        ..., description="Knowledge base name", examples=["samples"]
    ),
    override: bool = Field(False, description="Override existing files"),
    to_vector_store: bool = Field(True, description="Whether to vectorize after uploading the file"),
    chunk_size: int = Field(CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
    chunk_overlap: int = Field(OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
    zh_title_enhance: bool = Field(ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
    docs: str = Field("", description="Custom docs, must be converted to a JSON string"),
    not_refresh_vs_cache: bool = Field(False, description="Skip persisting the vector store for now (used for FAISS)"),
