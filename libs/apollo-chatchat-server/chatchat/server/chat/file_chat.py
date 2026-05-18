import asyncio
import json
import logging
import os
from typing import AsyncIterable, List, Optional

import nest_asyncio
from fastapi import Body, File, Form, UploadFile
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from sse_starlette.sse import EventSourceResponse

from chatchat.settings import Settings
from chatchat.server.chat.utils import History
from chatchat.server.knowledge_base.kb_cache.faiss_cache import memo_faiss_pool
from chatchat.server.knowledge_base.utils import KnowledgeFile
from chatchat.server.utils import (
    BaseResponse,
    get_ChatOpenAI,
    get_Embeddings,
    get_prompt_template,
    get_temp_dir,
    run_in_thread_pool,
    wrap_done,
)

from chatchat.utils import build_logger


logger = build_logger()


def _parse_files_in_thread(
    files: List[UploadFile],
    dir: str,
    zh_title_enhance: bool,
    chunk_size: int,
    chunk_overlap: int,
):
    """
    Use multiple threads to save uploaded files into the corresponding directory.
    The generator yields save results: [success or error, filename, msg, docs]
    """

    def parse_file(file: UploadFile) -> dict:
        """
        Save a single file.
        """
        try:
            filename = file.filename
            file_path = os.path.join(dir, filename)
            file_content = file.file.read()  # Read the uploaded file's contents

            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)
            kb_file = KnowledgeFile(filename=filename, knowledge_base_name="temp")
            kb_file.filepath = file_path
            docs = kb_file.file2text(
                zh_title_enhance=zh_title_enhance,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            return True, filename, f"Successfully uploaded file {filename}", docs
        except Exception as e:
            msg = f"Failed to upload file {filename}; error: {e}"
            return False, filename, msg, []

    params = [{"file": file} for file in files]
    for result in run_in_thread_pool(parse_file, params=params):
        yield result


def upload_temp_docs(
    files: List[UploadFile] = File(..., description="Files to upload; multiple files are supported"),
    prev_id: str = Form(None, description="Previous knowledge base ID"),
    chunk_size: int = Form(Settings.kb_settings.CHUNK_SIZE, description="Maximum length of a single text chunk in the knowledge base"),
    chunk_overlap: int = Form(Settings.kb_settings.OVERLAP_SIZE, description="Overlap length between adjacent text chunks in the knowledge base"),
    zh_title_enhance: bool = Form(Settings.kb_settings.ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
) -> BaseResponse:
    """
    Save files to a temporary directory and vectorize them.
    Returns the temporary directory name as the ID, which is also the ID of the temporary vector store.
    """
    if prev_id is not None:
        memo_faiss_pool.pop(prev_id)

    failed_files = []
    documents = []
    path, id = get_temp_dir(prev_id)
    for success, file, msg, docs in _parse_files_in_thread(
        files=files,
        dir=path,
        zh_title_enhance=zh_title_enhance,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    ):
        if success:
            documents += docs
        else:
            failed_files.append({file: msg})
    try:
        with memo_faiss_pool.load_vector_store(kb_name=id).acquire() as vs:
            vs.add_documents(documents)
    except Exception as e:
        logger.error(f"Failed to add documents to faiss: {e}")

    return BaseResponse(data={"id": id, "failed_files": failed_files})


async def file_chat(
    query: str = Body(..., description="User input", examples=["Hello"]),
    knowledge_id: str = Body(..., description="Temporary knowledge base ID"),
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
        examples=[
            [
                {"role": "user", "content": "Let's play an idiom chain game; I'll start with 'lively and energetic'"},
                {"role": "assistant", "content": "vivacious and spirited"},
            ]
        ],
    ),
    stream: bool = Body(False, description="Stream output"),
    model_name: str = Body(None, description="LLM model name."),
    temperature: float = Body(0.01, description="LLM sampling temperature", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        None, description="Cap on the number of tokens the LLM can generate; the default None means use the model's maximum"
    ),
    prompt_name: str = Body(
        "default",
        description="Name of the prompt template to use (configured in prompt_settings.yaml)",
    ),
):
    if knowledge_id not in memo_faiss_pool.keys():
        # return BaseResponse(code=404, msg=f"Temporary knowledge base {knowledge_id} not found; please upload files first")
        return BaseResponse(
            code=404,
            msg=f"""[Go!] Welcome to the [EIA Chat Assistant] trial\r\n
Please first upload files such as environmental impact assessment reports to enable features like preparation-behavior compliance checks and project risk evaluation analysis!""",
        )

    history = [History.from_data(h) for h in history]

    async def knowledge_base_chat_iterator() -> AsyncIterable[str]:
        try:
            nonlocal max_tokens
            callback = AsyncIteratorCallbackHandler()
            if isinstance(max_tokens, int) and max_tokens <= 0:
                max_tokens = None

            callbacks = [callback]
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

            model = get_ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                callbacks=callbacks,
            )
            embed_func = get_Embeddings()
            embeddings = await embed_func.aembed_query(query)
            with memo_faiss_pool.acquire(knowledge_id) as vs:
                docs = vs.similarity_search_with_score_by_vector(
                    embeddings, k=top_k, score_threshold=score_threshold
                )
                docs = [x[0] for x in docs]

            context = "\n".join([doc.page_content for doc in docs])
            if len(docs) == 0:  # If no relevant documents are found, use the Empty template
                prompt_template = get_prompt_template("rag", "empty")
            else:
                prompt_template = get_prompt_template("rag", "default")
            input_msg = History(role="user", content=prompt_template).to_msg_template(False)
            chat_prompt = ChatPromptTemplate.from_messages(
                [i.to_msg_template() for i in history] + [input_msg]
            )

            chain = LLMChain(prompt=chat_prompt, llm=model)

            # Begin a task that runs in the background.
            task = asyncio.create_task(
                wrap_done(
                    chain.acall({"context": context, "question": query}), callback.done
                ),
            )

            source_documents = []
            for inum, doc in enumerate(docs):
                filename = doc.metadata.get("source")
                text = f"""Source [{inum + 1}] [{filename}] \n\n{doc.page_content}\n\n"""
                source_documents.append(text)

            if len(source_documents) == 0:  # No relevant documents were found
                source_documents.append(
                    f"""<span style='color:red'>No relevant documents found; this answer is generated solely from the large model's own knowledge!</span>"""
                )

            if stream:
                async for token in callback.aiter():
                    # Use server-sent-events to stream the response
                    yield json.dumps({"answer": token}, ensure_ascii=False)
                yield json.dumps({"docs": source_documents}, ensure_ascii=False)
            else:
                answer = ""
                async for token in callback.aiter():
                    answer += token
                yield json.dumps(
                    {"answer": answer, "docs": source_documents}, ensure_ascii=False
                )
            await task
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return

    return EventSourceResponse(knowledge_base_chat_iterator())
