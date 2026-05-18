from typing import Union, List

from pydantic import BaseModel, Field
from open_chatcaht._constants import CHUNK_SIZE, OVERLAP_SIZE, ZH_TITLE_ENHANCE


class UploadTempDocsParam(BaseModel):
    prev_id: str = Field(None, description="Previous knowledge base ID"),
    chunk_size: int = Field(CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
    chunk_overlap: int = Field(OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
    zh_title_enhance: bool = Field(ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
