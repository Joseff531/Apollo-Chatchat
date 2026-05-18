from pydantic import BaseModel, Field


class ListKbDocsFileParam(BaseModel):
    knowledge_base_name: str = Field(description="Knowledge base name")
