from pydantic import BaseModel, Field


class UpdateKbInfoParam(BaseModel):
    knowledge_base_name: str = Field(
        ..., description="Knowledge base name", examples=["samples"]
    ),
    kb_info: str = Field(..., description="Knowledge base description", examples=["This is a knowledge base"]),
