from sqlalchemy import JSON, Column, DateTime, Integer, String, func

from chatchat.server.db.base import Base


class MessageModel(Base):
    """
    Chat message record model.
    """

    __tablename__ = "message"
    id = Column(String(32), primary_key=True, comment="Chat record ID")
    conversation_id = Column(String(32), default=None, index=True, comment="Conversation ID")
    chat_type = Column(String(50), comment="Chat type")
    query = Column(String(4096), comment="User query")
    response = Column(String(4096), comment="Model response")
    # Stores the knowledge base id and similar fields for future extensions
    meta_data = Column(JSON, default={})
    # Max score 100; higher values indicate better feedback
    feedback_score = Column(Integer, default=-1, comment="User feedback score")
    feedback_reason = Column(String(255), default="", comment="User feedback reason")
    create_time = Column(DateTime, default=func.now(), comment="Creation time")

    def __repr__(self):
        return f"<message(id='{self.id}', conversation_id='{self.conversation_id}', chat_type='{self.chat_type}', query='{self.query}', response='{self.response}',meta_data='{self.meta_data}',feedback_score='{self.feedback_score}',feedback_reason='{self.feedback_reason}', create_time='{self.create_time}')>"
