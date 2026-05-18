from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Request
from langchain.prompts.prompt import PromptTemplate
from sse_starlette import EventSourceResponse

from chatchat.server.api_server.api_schemas import OpenAIChatInput
from chatchat.server.chat.chat import chat
from chatchat.server.chat.kb_chat import kb_chat
from chatchat.server.chat.feedback import chat_feedback
from chatchat.server.chat.file_chat import file_chat
from chatchat.server.db.repository import add_message_to_db
from chatchat.server.utils import (
    get_OpenAIClient,
    get_prompt_template,
    get_tool,
    get_tool_config,
)
from chatchat.settings import Settings
from chatchat.utils import build_logger
from .openai_routes import openai_request, OpenAIChatOutput


logger = build_logger()

chat_router = APIRouter(prefix="/chat", tags=["ChatChat conversations"])

# chat_router.post(
#     "/chat",
#     summary="Talk with the LLM model (via LLMChain)",
# )(chat)

chat_router.post(
    "/feedback",
    summary="Submit a rating for an LLM model conversation",
)(chat_feedback)


chat_router.post("/kb_chat", summary="Knowledge base chat")(kb_chat)
chat_router.post("/file_chat", summary="File chat")(file_chat)


@chat_router.post("/chat/completions", summary="Unified chat endpoint compatible with OpenAI")
async def chat_completions(
    request: Request,
    body: OpenAIChatInput,
) -> Dict:
    """
    The request parameters mirror openai.chat.completions.create; additional parameters can be
    passed via extra_body. tools and tool_choice may also be passed as tool names directly,
    which will be converted based on the tools defined in this project.
    Different parameter combinations invoke different chat behaviors:
    - tool_choice
        - extra_body contains tool_input: directly invoke tool_choice(tool_input)
        - extra_body does not contain tool_input: invoke tool_choice via the agent
    - tools: agent chat
    - Otherwise: LLM chat
    More combinations (e.g., file chat) will be considered in the future.
    Returns a Dict compatible with OpenAI.
    """
    # import rich
    # rich.print(body)

    # When this endpoint is called without a "max_tokens" parameter in the body,
    # the value defined in the configuration is used by default.
    if body.max_tokens in [None, 0]:
        body.max_tokens = Settings.model_settings.MAX_TOKENS

    client = get_OpenAIClient(model_name=body.model, is_async=True)
    extra = {**body.model_extra} or {}
    for key in list(extra):
        delattr(body, key)

    # check tools & tool_choice in request body
    if isinstance(body.tool_choice, str):
        if t := get_tool(body.tool_choice):
            body.tool_choice = {"function": {"name": t.name}, "type": "function"}
    if isinstance(body.tools, list):
        for i in range(len(body.tools)):
            if isinstance(body.tools[i], str):
                if t := get_tool(body.tools[i]):
                    body.tools[i] = {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.args,
                        },
                    }

    conversation_id = extra.get("conversation_id")
  
    try:
        message_id = (
            add_message_to_db(
                chat_type="agent_chat",
                query=body.messages[-1]["content"],
                conversation_id=conversation_id,
            )
            if conversation_id
            else None
        )
    except Exception as e:
        logger.warning(f"failed to add message to db: {e}")
        message_id = None

    chat_model_config = {}  # TODO: support model configuration from the frontend
    tool_config = {}
    if body.tools:
        tool_names = [x["function"]["name"] for x in body.tools]
        tool_config = {name: get_tool_config(name) for name in tool_names}

    result = await chat(
        query=body.messages[-1]["content"],
        metadata=extra.get("metadata", {}),
        conversation_id=extra.get("conversation_id", ""),
        message_id=message_id,
        history_len=-1,
        stream=body.stream,
        chat_model_config=extra.get("chat_model_config", chat_model_config),
        tool_config=tool_config,
        use_mcp=extra.get("use_mcp", False),
        max_tokens=body.max_tokens,
    )
    return result
