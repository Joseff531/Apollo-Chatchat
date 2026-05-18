from fastapi import Body

from chatchat.utils import build_logger
from chatchat.server.db.repository import get_human_message_event_by_id, update_human_message_event, \
    add_human_message_event_to_db, list_human_message_event
from chatchat.server.utils import BaseResponse

logger = build_logger()


def function_calls(
    call_id: str = Body("", description="call_id"),
    conversation_id: str = Body("", description="Conversation ID"),
    function_name: str = Body("", description="Function Name"),
    kwargs: str = Body("", description="parameters"),
    comment: str = Body("", description="User comment"),
    action: str = Body("", description="User action")
):
    """
    Add a new human feedback message event
    """
    try:
        add_human_message_event_to_db(call_id,conversation_id, function_name, kwargs,comment, action)
    except Exception as e:
        msg = f"Error adding human feedback message event: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)
    return BaseResponse(code=200, msg=f"Feedback submitted for chat record {call_id}", data={"call_id": call_id})


def get_function_call(call_id: str):
    """
    Query a human feedback message event
    """
    try:
        return get_human_message_event_by_id(call_id)
    except Exception as e:
        msg = f"Error querying human feedback message event: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)


def respond_function_call(call_id: str, comment: str, action: str):
    """
    Update an existing human feedback message event
    """
    try:
        update_human_message_event(call_id, comment, action)
    except Exception as e:
        msg = f"Error updating existing human feedback message event: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)
    return BaseResponse(code=200, msg=f"Chat record {call_id} updated")
