from __future__ import annotations

import asyncio, json
import uuid
from typing import AsyncIterable, List, Optional, Literal

from fastapi import Body, Request
from fastapi.concurrency import run_in_threadpool
from sse_starlette.sse import EventSourceResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.prompts.chat import ChatPromptTemplate


from chatchat.settings import Settings
from chatchat.server.agent.tools_factory.search_internet import search_engine
from chatchat.server.api_server.api_schemas import OpenAIChatOutput
from chatchat.server.chat.utils import History
from chatchat.server.knowledge_base.kb_service.base import KBServiceFactory
from chatchat.server.knowledge_base.kb_doc_api import search_docs, search_temp_docs
from chatchat.server.knowledge_base.utils import format_reference
from chatchat.server.utils import (wrap_done, get_ChatOpenAI, get_default_llm,
                                   BaseResponse, get_prompt_template, build_logger,
                                   check_embed_model, api_address
                                )


logger = build_logger()


async def kb_chat(query: str = Body(..., description="User input", examples=["Hello"]),
                mode: Literal["local_kb", "temp_kb", "search_engine"] = Body("local_kb", description="Knowledge source"),
                kb_name: str = Body("", description="When mode=local_kb this is the knowledge base name; when temp_kb it is the temporary knowledge base ID; when search_engine it is the search engine name", examples=["samples"]),
                top_k: int = Body(Settings.kb_settings.VECTOR_SEARCH_TOP_K, description="Number of matching vectors"),
                score_threshold: float = Body(
                    Settings.kb_settings.SCORE_THRESHOLD,
                    description="Knowledge base relevance threshold; range 0-1, lower SCORE means higher relevance; 1 is equivalent to no filtering. Around 0.5 is recommended.",
                    ge=0,
                    le=2,
                ),
                history: List[History] = Body(
                    [],
                    description="Conversation history",
                    examples=[[
                        {"role": "user",
                        "content": "Let's play an idiom chain game; I'll start with 'lively and energetic'"},
                        {"role": "assistant",
                        "content": "vivacious and spirited"}]]
                ),
                stream: bool = Body(True, description="Stream output"),
                model: str = Body(get_default_llm(), description="LLM model name."),
                temperature: float = Body(Settings.model_settings.TEMPERATURE, description="LLM sampling temperature", ge=0.0, le=2.0),
                max_tokens: Optional[int] = Body(
                    Settings.model_settings.MAX_TOKENS,
                    description="Cap on the number of tokens the LLM can generate; the default None means use the model's maximum"
                ),
                prompt_name: str = Body(
                    "default",
                    description="Name of the prompt template to use (configured in prompt_settings.yaml)"
                ),
                return_direct: bool = Body(False, description="Return retrieval results directly without sending them to the LLM"),
                request: Request = None,
                ):
    if mode == "local_kb":
        kb = KBServiceFactory.get_service_by_name(kb_name)
        if kb is None:
            return BaseResponse(code=404, msg=f"Knowledge base {kb_name} not found")
    
    async def knowledge_base_chat_iterator() -> AsyncIterable[str]:
        try:
            nonlocal history, prompt_name, max_tokens

            history = [History.from_data(h) for h in history]

            if mode == "local_kb":
                kb = KBServiceFactory.get_service_by_name(kb_name)
                ok, msg = kb.check_embed_model()
                if not ok:
                    raise ValueError(msg)
                docs = await run_in_threadpool(search_docs,
                                                query=query,
                                                knowledge_base_name=kb_name,
                                                top_k=top_k,
                                                score_threshold=score_threshold,
                                                file_name="",
                                                metadata={})
                source_documents = format_reference(kb_name, docs, api_address(is_public=True))
            elif mode == "temp_kb":
                ok, msg = check_embed_model()
                if not ok:
                    raise ValueError(msg)
                docs = await run_in_threadpool(search_temp_docs,
                                                kb_name,
                                                query=query,
                                                top_k=top_k,
                                                score_threshold=score_threshold)
                source_documents = format_reference(kb_name, docs, api_address(is_public=True))
            elif mode == "search_engine":
                result = await run_in_threadpool(search_engine, query, top_k, kb_name)
                docs = [x.dict() for x in result.get("docs", [])]
                source_documents = [f"""Source [{i + 1}] [{d['metadata']['filename']}]({d['metadata']['source']}) \n\n{d['page_content']}\n\n""" for i,d in enumerate(docs)]
            else:
                docs = []
                source_documents = []
            # import rich
            # rich.print(dict(
            #     mode=mode,
            #     query=query,
            #     knowledge_base_name=kb_name,
            #     top_k=top_k,
            #     score_threshold=score_threshold,
            # ))
            # rich.print(docs)
            if return_direct:
                yield OpenAIChatOutput(
                    id=f"chat{uuid.uuid4()}",
                    model=None,
                    object="chat.completion",
                    content="",
                    role="assistant",
                    finish_reason="stop",
                    docs=source_documents,
                ) .model_dump_json()
                return

            callback = AsyncIteratorCallbackHandler()
            callbacks = [callback]

            # Enable langchain-chatchat to support langfuse
            import os
            langfuse_secret_key = os.environ.get('LANGFUSE_SECRET_KEY')
            langfuse_public_key = os.environ.get('LANGFUSE_PUBLIC_KEY')
            langfuse_host = os.environ.get('LANGFUSE_HOST')
            if langfuse_secret_key and langfuse_public_key and langfuse_host :
                from langfuse import Langfuse
                from langfuse.callback import CallbackHandler
                langfuse_handler = CallbackHandler()
                callbacks.append(langfuse_handler)

            if max_tokens in [None, 0]:
                max_tokens = Settings.model_settings.MAX_TOKENS

            llm = get_ChatOpenAI(
                model_name=model,
                temperature=temperature,
                max_tokens=max_tokens,
                callbacks=callbacks,
            )
            # TODO: use the API as appropriate
            # # add reranker
            # if Settings.kb_settings.USE_RERANKER:
            #     reranker_model_path = get_model_path(Settings.kb_settings.RERANKER_MODEL)
            #     reranker_model = LangchainReranker(top_n=top_k,
            #                                     device=embedding_device(),
            #                                     max_length=Settings.kb_settings.RERANKER_MAX_LENGTH,
            #                                     model_name_or_path=reranker_model_path
            #                                     )
            #     print("-------------before rerank-----------------")
            #     print(docs)
            #     docs = reranker_model.compress_documents(documents=docs,
            #                                              query=query)
            #     print("------------after rerank------------------")
            #     print(docs)
            context = "\n\n".join([doc["page_content"] for doc in docs])

            if len(docs) == 0:  # If no relevant documents are found, use the empty template
                prompt_name = "empty"
            prompt_template = get_prompt_template("rag", prompt_name)
            input_msg = History(role="user", content=prompt_template).to_msg_template(False)
            chat_prompt = ChatPromptTemplate.from_messages(
                [i.to_msg_template() for i in history] + [input_msg])

            chain = chat_prompt | llm

            # Begin a task that runs in the background.
            task = asyncio.create_task(wrap_done(
                chain.ainvoke({"context": context, "question": query}),
                callback.done),
            )

            if len(source_documents) == 0:  # No relevant documents were found
                source_documents.append(f"<span style='color:red'>No relevant documents found; this answer is generated solely from the large model's own knowledge!</span>")

            if stream:
                # yield documents first
                ret = OpenAIChatOutput(
                    id=f"chat{uuid.uuid4()}",
                    object="chat.completion.chunk",
                    content="",
                    role="assistant",
                    model=model,
                    docs=source_documents,
                )
                yield ret.model_dump_json()

                async for token in callback.aiter():
                    ret = OpenAIChatOutput(
                        id=f"chat{uuid.uuid4()}",
                        object="chat.completion.chunk",
                        content=token,
                        role="assistant",
                        model=model,
                    )
                    yield ret.model_dump_json()
            else:
                answer = ""
                async for token in callback.aiter():
                    answer += token
                ret = OpenAIChatOutput(
                    id=f"chat{uuid.uuid4()}",
                    object="chat.completion",
                    content=answer,
                    role="assistant",
                    model=model,
                )
                yield ret.model_dump_json()
            await task
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return
        except Exception as e:
            logger.error(f"error in knowledge chat: {e}")
            yield {"data": json.dumps({"error": str(e)})}
            return

    if stream:
        return EventSourceResponse(knowledge_base_chat_iterator())
    else:
        return await knowledge_base_chat_iterator().__anext__()
