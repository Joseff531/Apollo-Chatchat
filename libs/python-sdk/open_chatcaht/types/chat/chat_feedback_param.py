from pydantic import Field, BaseModel


class ChatFeedbackParam(BaseModel):
    message_id: str = Field("", max_length=32, description="Chat record ID"),
    score: int = Field(0, max=100, description="User rating, out of 100. Higher means better rating"),
    reason: str = Field("", description="User rating reason, e.g. inconsistent with facts"),
