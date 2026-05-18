import asyncio
import json
from typing import List, Optional

from fastapi import Body
from sse_starlette import EventSourceResponse

from chatchat.settings import Settings
from chatchat.server.knowledge_base.kb_service.base import KBServiceFactory
from chatchat.server.knowledge_base.kb_summary.base import KBSummaryService
from chatchat.server.knowledge_base.kb_summary.summary_chunk import SummaryAdapter
from chatchat.server.knowledge_base.model.kb_document_model import DocumentWithVSId
from chatchat.server.knowledge_base.utils import list_files_from_folder
from chatchat.server.utils import BaseResponse, get_ChatOpenAI, wrap_done, get_default_embedding
from chatchat.utils import build_logger


logger = build_logger()

def recreate_summary_vector_store(
    knowledge_base_name: str = Body(..., examples=["samples"]),
    allow_empty_kb: bool = Body(True),
    vs_type: str = Body(Settings.kb_settings.DEFAULT_VS_TYPE),
    embed_model: str = Body(get_default_embedding()),
    file_description: str = Body(""),
    model_name: str = Body(None, description="LLM model name."),
    temperature: float = Body(0.01, description="LLM sampling temperature", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        None, description="Limit the number of tokens the LLM generates; default None means the model's maximum"
    ),
):
    """
    Rebuild the file summary for a single knowledge base
    :param max_tokens:
    :param model_name:
    :param temperature:
    :param file_description:
    :param knowledge_base_name:
    :param allow_empty_kb:
    :param vs_type:
    :param embed_model:
    :return:
    """
    if max_tokens in [None, 0]:
        max_tokens = Settings.model_settings.MAX_TOKENS

    def output():
        try:
            kb = KBServiceFactory.get_service(knowledge_base_name, vs_type, embed_model)
            if not kb.exists() and not allow_empty_kb:
                yield {"code": 404, "msg": f"Knowledge base '{knowledge_base_name}' not found"}
            else:
                ok, msg = kb.check_embed_model()
                if not ok:
                    yield {"code": 404, "msg": msg}
                else:
                    # Recreate the knowledge base
                    kb_summary = KBSummaryService(knowledge_base_name, embed_model)
                    kb_summary.drop_kb_summary()
                    kb_summary.create_kb_summary()

                    llm = get_ChatOpenAI(
                        model_name=model_name,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        local_wrap=True,
                    )
                    reduce_llm = get_ChatOpenAI(
                        model_name=model_name,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        local_wrap=True,
                    )
                    # Text summary adapter
                    summary = SummaryAdapter.form_summary(
                        llm=llm, reduce_llm=reduce_llm, overlap_size=Settings.kb_settings.OVERLAP_SIZE
                    )
                    files = list_files_from_folder(knowledge_base_name)

                    i = 0
                    for i, file_name in enumerate(files):
                        doc_infos = kb.list_docs(file_name=file_name)
                        docs = summary.summarize(
                            file_description=file_description, docs=doc_infos
                        )

                        status_kb_summary = kb_summary.add_kb_summary(
                            summary_combine_docs=docs
                        )
                        if status_kb_summary:
                            logger.info(f"({i + 1} / {len(files)}): {file_name} summary complete")
                            yield json.dumps(
                                {
                                    "code": 200,
                                    "msg": f"({i + 1} / {len(files)}): {file_name}",
                                    "total": len(files),
                                    "finished": i + 1,
                                    "doc": file_name,
                                },
                                ensure_ascii=False,
                            )
                        else:
                            msg = f"Error summarizing file '{file_name}' for knowledge base '{knowledge_base_name}'. Skipped."
                            logger.error(msg)
                            yield json.dumps(
                                {
                                    "code": 500,
                                    "msg": msg,
                                }
                            )
                        i += 1
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return

    return EventSourceResponse(output())


def summary_file_to_vector_store(
    knowledge_base_name: str = Body(..., examples=["samples"]),
    file_name: str = Body(..., examples=["test.pdf"]),
    allow_empty_kb: bool = Body(True),
    vs_type: str = Body(Settings.kb_settings.DEFAULT_VS_TYPE),
    embed_model: str = Body(get_default_embedding()),
    file_description: str = Body(""),
    model_name: str = Body(None, description="LLM model name."),
    temperature: float = Body(0.01, description="LLM sampling temperature", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        None, description="Limit the number of tokens the LLM generates; default None means the model's maximum"
    ),
):
    """
    Summarize a single knowledge base by file name
    :param model_name:
    :param max_tokens:
    :param temperature:
    :param file_description:
    :param file_name:
    :param knowledge_base_name:
    :param allow_empty_kb:
    :param vs_type:
    :param embed_model:
    :return:
    """

    def output():
        try:
            kb = KBServiceFactory.get_service(knowledge_base_name, vs_type, embed_model)
            if not kb.exists() and not allow_empty_kb:
                yield {"code": 404, "msg": f"Knowledge base '{knowledge_base_name}' not found"}
            else:
                # Recreate the knowledge base
                kb_summary = KBSummaryService(knowledge_base_name, embed_model)
                kb_summary.create_kb_summary()

                llm = get_ChatOpenAI(
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    local_wrap=True,
                )
                reduce_llm = get_ChatOpenAI(
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    local_wrap=True,
                )
                # Text summary adapter
                summary = SummaryAdapter.form_summary(
                    llm=llm, reduce_llm=reduce_llm, overlap_size=Settings.kb_settings.OVERLAP_SIZE
                )

                doc_infos = kb.list_docs(file_name=file_name)
                docs = summary.summarize(file_description=file_description, docs=doc_infos)

                status_kb_summary = kb_summary.add_kb_summary(summary_combine_docs=docs)
                if status_kb_summary:
                    logger.info(f" {file_name} summary complete")
                    yield json.dumps(
                        {
                            "code": 200,
                            "msg": f"{file_name} summary complete",
                            "doc": file_name,
                        },
                        ensure_ascii=False,
                    )
                else:
                    msg = f"Error summarizing file '{file_name}' for knowledge base '{knowledge_base_name}'. Skipped."
                    logger.error(msg)
                    yield json.dumps(
                        {
                            "code": 500,
                            "msg": msg,
                        }
                    )
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return

    return EventSourceResponse(output())


def summary_doc_ids_to_vector_store(
    knowledge_base_name: str = Body(..., examples=["samples"]),
    doc_ids: List = Body([], examples=[["uuid"]]),
    vs_type: str = Body(Settings.kb_settings.DEFAULT_VS_TYPE),
    embed_model: str = Body(get_default_embedding()),
    file_description: str = Body(""),
    model_name: str = Body(None, description="LLM model name."),
    temperature: float = Body(0.01, description="LLM sampling temperature", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        None, description="Limit the number of tokens the LLM generates; default None means the model's maximum"
    ),
) -> BaseResponse:
    """
    Summarize a single knowledge base by doc_ids
    :param knowledge_base_name:
    :param doc_ids:
    :param model_name:
    :param max_tokens:
    :param temperature:
    :param file_description:
    :param vs_type:
    :param embed_model:
    :return:
    """
    kb = KBServiceFactory.get_service(knowledge_base_name, vs_type, embed_model)
    if not kb.exists():
        return BaseResponse(
            code=404, msg=f"Knowledge base not found: {knowledge_base_name}", data={}
        )
    else:
        llm = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            local_wrap=True,
        )
        reduce_llm = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            local_wrap=True,
        )
        # Text summary adapter
        summary = SummaryAdapter.form_summary(
            llm=llm, reduce_llm=reduce_llm, overlap_size=Settings.kb_settings.OVERLAP_SIZE
        )

        doc_infos = kb.get_doc_by_ids(ids=doc_ids)
        # Convert doc_infos into objects wrapped by DocumentWithVSId
        doc_info_with_ids = [
            DocumentWithVSId(**{**doc.dict(), "id":with_id})
            for with_id, doc in zip(doc_ids, doc_infos)
        ]

        docs = summary.summarize(
            file_description=file_description, docs=doc_info_with_ids
        )

        # Convert docs to dict
        resp_summarize = [{**doc.dict()} for doc in docs]

        return BaseResponse(
            code=200, msg="Summary complete", data={"summarize": resp_summarize}
        )
