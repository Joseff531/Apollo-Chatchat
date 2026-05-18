# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.
from typing import Literal

import httpx

RAW_RESPONSE_HEADER = "X-Stainless-Raw-Response"
OVERRIDE_CAST_TO_HEADER = "____stainless_override_cast_to"

# default timeout is 10 minutes
DEFAULT_TIMEOUT = httpx.Timeout(timeout=600.0, connect=5.0)
DEFAULT_MAX_RETRIES = 2
DEFAULT_CONNECTION_LIMITS = httpx.Limits(max_connections=1000, max_keepalive_connections=100)

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0

EMBEDDING_MODEL: str = "bge-large-zh-v1.5"
HTTPX_TIMEOUT: float = 10.0
API_BASE_URI: str = 'http://127.0.0.1:7861/'

# Knowledge base related
"""Maximum length of a single text segment in the knowledge base (does not apply to MarkdownHeaderTextSplitter)"""
CHUNK_SIZE: int = 250
"""Overlap length between adjacent text segments in the knowledge base (does not apply to MarkdownHeaderTextSplitter)"""
OVERLAP_SIZE: int = 50
"""Whether to enable Chinese title enhancement, and related configuration for title enhancement"""
ZH_TITLE_ENHANCE: bool = False
"""Number of matching vectors returned from the knowledge base"""
VECTOR_SEARCH_TOP_K: int = 3  # TODO: duplicate with tool config item
"""Knowledge base matching relevance threshold, value range between 0-2. Smaller SCORE means higher relevance; a value of 2 effectively disables filtering. Recommended around 0.5"""
SCORE_THRESHOLD: float = 0.4
"""Default vector store / full-text search engine type"""
VS_TYPE: Literal["faiss", "milvus", "zilliz", "pg", "es", "relyt", "chromadb"] = "faiss"
# llm
TEMPERATURE: float = 0.7
LLM_MODEL = "chatglm-6b"
MAX_TOKENS = 2048

