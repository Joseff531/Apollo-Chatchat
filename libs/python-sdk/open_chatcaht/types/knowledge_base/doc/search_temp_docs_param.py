from pydantic import BaseModel, Field

from open_chatcaht._constants import VECTOR_SEARCH_TOP_K, SCORE_THRESHOLD


class SearchTempDocsParam(BaseModel):
    knowledge_id: str
    query: str
    top_k: int = Field(default=VECTOR_SEARCH_TOP_K, description="Number of matching vectors")
    score_threshold: float = Field(default=SCORE_THRESHOLD,
                                   ge=0.0,
                                   le=1.0,
                                   description="Knowledge base matching relevance threshold, value range between 0-1. "
                                               "Smaller SCORE means higher relevance; "
                                               "a value of 1 effectively disables filtering. Recommended around 0.5")
