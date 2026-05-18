import asyncio
import json
import uuid
import os
from chatchat.server.db.repository.message_repository import filter_message
from typing import AsyncIterable, List, Union, Tuple
from langchain_core.load import dumpd, dumps, load, loads

from fastapi import Body
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate

from chatchat.server.agents_registry.agents_registry import agents_registry
from sse_starlette.sse import EventSourceResponse

from chatchat.server.db.repository.mcp_connection_repository import get_enabled_mcp_connections
from chatchat.settings import Settings
from chatchat.server.api_server.api_schemas import OpenAIChatOutput
from langchain_chatchat.callbacks.agent_callback_handler import (
    AgentExecutorAsyncIteratorCallbackHandler,
    AgentStatus,
)
from langchain_chatchat.agents.platform_tools import PlatformToolsAction, PlatformToolsFinish, \
    PlatformToolsActionToolStart, PlatformToolsActionToolEnd, PlatformToolsLLMStatus
from chatchat.server.chat.utils import History
from chatchat.server.db.repository import add_message_to_db, update_message

from langchain_chatchat import ChatPlatformAI, PlatformToolsRunnable
from chatchat.server.utils import (
    MsgType,
    get_ChatOpenAI,
    get_prompt_template,
    get_tool,
    wrap_done,
    get_default_llm,
    build_logger,
    get_ChatPlatformAIParams
)

logger = build_logger()


def create_models_from_config(configs, callbacks, stream, max_tokens):
    configs = configs or Settings.model_settings.LLM_MODEL_CONFIG
    models = {}
    prompts = {}
    for model_type, params in configs.items():
        model_name = params.get("model", "").strip() or get_default_llm()
        callbacks = callbacks if params.get("callbacks", False) else None
        # Decide whether max_tokens was supplied: if so use that value (API call with explicit value);
        # otherwise fall back to the value defined in the configuration (UI call, or API call without it).
        max_tokens_value = max_tokens if max_tokens is not None else params.get("max_tokens", 1000)
        if model_type == "action_model":

            llm_params = get_ChatPlatformAIParams(
                model_name=model_name,
                temperature=params.get("temperature", 0.5),
                max_tokens=max_tokens_value,
            )
            model_instance = ChatPlatformAI(**llm_params)
        else:
            model_instance = get_ChatOpenAI(
                model_name=model_name,
                temperature=params.get("temperature", 0.5),
                max_tokens=max_tokens_value,
                callbacks=callbacks,
                streaming=stream,
                local_wrap=True,
            )
        models[model_type] = model_instance
        prompt_name = params.get("prompt_name", "default")
        prompt_template = get_prompt_template(type=model_type, name=prompt_name)
        prompts[model_type] = prompt_template
    return models, prompts


def create_models_chains(
    history_len, prompts, models, tools, callbacks, conversation_id, metadata,  use_mcp: bool = False
):

    # Fetch the intermediate_steps and mcp_connections associated with the conversation_id from the database
    messages = filter_message(
        conversation_id=conversation_id, limit=history_len
    )
    # Returned records are in reverse chronological order; reverse them to chronological order
    messages = list(reversed(messages))
    history: List[Union[List, Tuple]] = []
    for message in messages:
        history.append({"role": "user", "content": message["query"]})
        history.append({"role": "assistant", "content":  message["response"]})

    intermediate_steps = loads(messages[-1].get("metadata", {}).get("intermediate_steps"), valid_namespaces=["langchain_chatchat", "agent_toolkits", "all_tools", "tool"] )  if len(messages)>0 and messages[-1].get("metadata") is not None else []
    llm = models["action_model"]
    llm.callbacks = callbacks
    connections = get_enabled_mcp_connections()

    # Convert to MCP connection format, supporting both StdioConnection and SSEConnection types
    mcp_connections = {}
    for conn in connections:
        if conn["transport"] == "stdio":
            # StdioConnection type
            mcp_connections[conn["server_name"]] = {
                "transport": "stdio",
                "command": conn["config"].get("command", conn["args"][0] if conn["args"] else ""),
                "args": conn["args"][1:] if len(conn["args"]) > 1 else [],
                "env": conn["env"],
                "encoding": "utf-8",
                "encoding_error_handler": "strict"
            }
        elif conn["transport"] == "sse":
            # SSEConnection type
            mcp_connections[conn["server_name"]] = {
                "transport": "sse",
                "url": conn["config"].get("url", ""),
                "headers": conn["config"].get("headers", {}),
                "timeout": conn.get("timeout", 30.0),
                "sse_read_timeout": conn.get("sse_read_timeout", 60.0)
            }
    
    agent_executor = PlatformToolsRunnable.create_agent_executor(
        agent_type="platform-knowledge-mode",
        agents_registry=agents_registry,
        llm=llm,
        tools=tools,
        history=history,
        intermediate_steps=intermediate_steps,
        mcp_connections=mcp_connections if use_mcp else {}
    )

    full_chain = {"chat_input": lambda x: x["input"]} | agent_executor

    return full_chain, agent_executor


async def chat(
        query: str = Body(..., description="User input", examples=["enraged and humiliated"]),
        metadata: dict = Body({}, description="Attachment; may be an image or another feature", examples=[]),
        conversation_id: str = Body("", description="Conversation ID"),
        message_id: str = Body(None, description="Database message ID"),
        history_len: int = Body(-1, description="Number of history messages to fetch from the database"),
        stream: bool = Body(True, description="Stream output"),
        chat_model_config: dict = Body({}, description="LLM model configuration", examples=[]),
        tool_config: dict = Body({}, description="Tool configuration", examples=[]),
        use_mcp: bool = Body(False, description="Use MCP"),
        max_tokens: int = Body(None, description="Maximum number of tokens the LLM may generate", example=4096),
):
    """Agent chat"""

    async def chat_iterator_event() -> AsyncIterable[OpenAIChatOutput]:
        try:
            callbacks = []

            # Enable langchain-chatchat to support langfuse
            import os

            langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
            langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
            langfuse_host = os.environ.get("LANGFUSE_HOST")
            if langfuse_secret_key and langfuse_public_key and langfuse_host:
                from langfuse import Langfuse
                from langfuse.callback import CallbackHandler

                langfuse_handler = CallbackHandler()
                callbacks.append(langfuse_handler)

            models, prompts = create_models_from_config(
                callbacks=callbacks, configs=chat_model_config, stream=stream, max_tokens=max_tokens
            )
            all_tools = get_tool().values()
            tools = [tool for tool in all_tools if tool.name in tool_config]
            tools = [t.copy(update={"callbacks": callbacks}) for t in tools]
            full_chain, agent_executor = create_models_chains(
                prompts=prompts,
                models=models,
                conversation_id=conversation_id,
                tools=tools,
                callbacks=callbacks,
                history_len=history_len,
                metadata=metadata,
                use_mcp = use_mcp
            )
            message_id = add_message_to_db(
                    chat_type="llm_chat",
                    query=query,
                    conversation_id=conversation_id,
            )
            chat_iterator = full_chain.invoke({
                "input": query
            })
            last_tool = {}
            async for item in chat_iterator:

                data = {}

                data["status"] = item.status
                data["tool_calls"] = []
                data["message_type"] = MsgType.TEXT
                if isinstance(item, PlatformToolsAction):
                    logger.info("PlatformToolsAction:" + str(item.to_json()))
                    data["text"] = item.log
                    tool_call = {
                        "index": 0,
                        "id": item.run_id,
                        "type": "function",
                        "function": {
                            "name": item.tool,
                            "arguments": item.tool_input,
                        },
                        "tool_output": None,
                        "is_error": False,
                    }
                    data["tool_calls"].append(tool_call)

                elif isinstance(item, PlatformToolsFinish):
                    data["text"] = item.log

                    last_tool.update(
                        tool_output=item.return_values["output"],
                    )
                    data["tool_calls"].append(last_tool)

                    try:
                        tool_output = json.loads(item.return_values["output"])
                        if message_type := tool_output.get("message_type"):
                            data["message_type"] = message_type
                    except:
                        ...

                elif isinstance(item, PlatformToolsActionToolStart):
                    logger.info("PlatformToolsActionToolStart:" + str(item.to_json()))

                    last_tool = {
                        "index": 0,
                        "id": item.run_id,
                        "type": "function",
                        "function": {
                            "name": item.tool,
                            "arguments": item.tool_input,
                        },
                        "tool_output": None,
                        "is_error": False,
                    }
                    data["tool_calls"].append(last_tool)

                elif isinstance(item, PlatformToolsActionToolEnd):
                    logger.info("PlatformToolsActionToolEnd:" + str(item.to_json()))
                    last_tool.update(
                        tool_output=item.tool_output,
                        is_error=False,
                    )
                    data["tool_calls"] = [last_tool]

                    last_tool = {}
                    try:
                        tool_output = json.loads(item.tool_output)
                        if message_type := tool_output.get("message_type"):
                            data["message_type"] = message_type
                    except:
                        ...
                elif isinstance(item, PlatformToolsLLMStatus):

                    data["text"] = item.text

                ret = OpenAIChatOutput(
                    id=f"chat{uuid.uuid4()}",
                    object="chat.completion.chunk",
                    content=data.get("text", ""),
                    role="assistant",
                    tool_calls=data["tool_calls"],
                    model=models["llm_model"].model_name,
                    status=data["status"],
                    message_type=data["message_type"],
                    message_id=message_id,
                    class_name=item.class_name()
                )
                yield ret.model_dump_json()

            string_intermediate_steps = dumps(agent_executor.intermediate_steps, pretty=True)

            update_message(
                message_id, 
                agent_executor.history[-1].get("content"),
                metadata = {
                    "intermediate_steps": string_intermediate_steps
                }
            )
             
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return
        except Exception as e:
            logger.error(f"error in chat: {e}")
            yield {"data": json.dumps({"error": str(e)})}
            return

    if stream:
        return EventSourceResponse(chat_iterator_event())
    else:
        ret = OpenAIChatOutput(
            id=f"chat{uuid.uuid4()}",
            object="chat.completion",
            content="",
            role="assistant",
            finish_reason="stop",
            tool_calls=[],
            status=AgentStatus.agent_finish,
            message_type=MsgType.TEXT,
            message_id=message_id,
        )

        async for chunk in chat_iterator_event():
            data = json.loads(chunk)
            if text := data["choices"][0]["delta"]["content"]:
                ret.content += text
            if data["status"] == AgentStatus.tool_end:
                ret.tool_calls += data["choices"][0]["delta"]["tool_calls"]
            ret.model = data["model"]
            ret.created = data["created"]

        return ret.model_dump()