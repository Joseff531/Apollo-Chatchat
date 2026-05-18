from typing import List

from pydantic import BaseModel, Field


class DownloadKbDocParam(BaseModel):
    knowledge_base_name: str = Field(
        ..., description="Knowledge base name", examples=["samples"]
    ),
    file_name: str = Field(..., description="File name", examples=["test.txt"]),
    preview: bool = Field(False, description="Yes: preview in browser; No: download"),
