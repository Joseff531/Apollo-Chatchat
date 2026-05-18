from pydantic import BaseModel, Field

from open_chatcaht._constants import VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD


class SearchKbDocsParam(BaseModel):
    query: str = Field(description="Search query")
    knowledge_base_name: str = Field(description="Knowledge base name")
    top_k: int = Field(default=VECTOR_SEARCH_TOP_K, description="Number of matching vectors")
    score_threshold: float = Field(default=SCORE_THRESHOLD,
                                   ge=0.0,
                                   le=1.0,
                                   description="Knowledge base matching relevance threshold, value range between 0-1. "
                                               "Smaller SCORE means higher relevance; "
                                               "a value of 1 effectively disables filtering. Recommended around 0.5")
    file_name: str = Field("", description="File name, supports SQL wildcards"),
    metadata: dict = Field({}, description="Filter by metadata, supports only top-level keys"),
