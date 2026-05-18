from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, func

from chatchat.server.db.base import Base


class KnowledgeBaseModel(Base):
    """
    Knowledge base model.
    """

    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="Knowledge base ID")
    kb_name = Column(String(50), comment="Knowledge base name")
    kb_info = Column(String(200), comment="Knowledge base description (used by Agent)")
    vs_type = Column(String(50), comment="Vector store type")
    embed_model = Column(String(50), comment="Embedding model name")
    file_count = Column(Integer, default=0, comment="File count")
    create_time = Column(DateTime, default=func.now(), comment="Creation time")

    def __repr__(self):
        return f"<KnowledgeBase(id='{self.id}', kb_name='{self.kb_name}',kb_intro='{self.kb_info} vs_type='{self.vs_type}', embed_model='{self.embed_model}', file_count='{self.file_count}', create_time='{self.create_time}')>"


# Create a corresponding Pydantic model
class KnowledgeBaseSchema(BaseModel):
    id: int
    kb_name: str
    kb_info: Optional[str]
    vs_type: Optional[str]
    embed_model: Optional[str]
    file_count: Optional[int]
    create_time: Optional[datetime]

    class Config:
        from_attributes = True  # Ensure validation can be performed from ORM instances
