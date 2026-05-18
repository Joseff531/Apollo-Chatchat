from fastapi import Body

from chatchat.utils import build_logger
from chatchat.server.db.repository import feedback_message_to_db
from chatchat.server.utils import BaseResponse

logger = build_logger()


def chat_feedback(
    message_id: str = Body("", max_length=32, description="Chat record id"),
    score: int = Body(0, max=100, description="User rating; out of 100, higher means better"),
    reason: str = Body("", description="Reason for the user's rating, e.g. factual errors"),
):
    try:
        feedback_message_to_db(message_id, score, reason)
    except Exception as e:
        msg = f"Error submitting chat record feedback: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=200, msg=f"Feedback submitted for chat record {message_id}")
