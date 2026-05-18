import asyncio
import json
import os
import urllib
from typing import Dict, List

from fastapi import Body, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from langchain.docstore.document import Document
from sse_starlette import EventSourceResponse

from chatchat.settings import Settings
from chatchat.server.db.repository.knowledge_file_repository import get_file_detail
from chatchat.server.knowledge_base.kb_service.base import (
    KBServiceFactory,
    get_kb_file_details,
)
from chatchat.server.knowledge_base.model.kb_document_model import DocumentWithVSId
from chatchat.server.knowledge_base.utils import (
    KnowledgeFile,
    files2docs_in_thread,
    get_file_path,
    list_files_from_folder,
    validate_kb_name,
)
from chatchat.server.knowledge_base.kb_cache.faiss_cache import memo_faiss_pool
from chatchat.server.utils import (
    BaseResponse,
    ListResponse,
    check_embed_model,
    run_in_thread_pool,
    get_default_embedding,
)
from chatchat.utils import build_logger

logger = build_logger()


def search_temp_docs(knowledge_id: str = Body(..., description="Knowledge base ID", examples=["example_id"]),
                     query: str = Body("", description="User input", examples=["hello"]),
                     top_k: int = Body(..., description="Number of documents to return", examples=[5]),
                     score_threshold: float = Body(..., description="Score threshold", examples=[0.8])) -> List[Dict]:
    '''Retrieve documents from the temporary FAISS knowledge base, used for file chat'''
    with memo_faiss_pool.acquire(knowledge_id) as vs:
        docs = vs.similarity_search_with_score(
            query, k=top_k, score_threshold=score_threshold
        )
        docs = [x[0].dict() for x in docs]
        return docs


def search_docs(
        query: str = Body("", description="User input", examples=["hello"]),
        knowledge_base_name: str = Body(
            ..., description="Knowledge base name", examples=["samples"]
        ),
        top_k: int = Body(Settings.kb_settings.VECTOR_SEARCH_TOP_K, description="Number of matched vectors"),
        score_threshold: float = Body(
            Settings.kb_settings.SCORE_THRESHOLD,
            description="Knowledge base match relevance threshold, value range is 0-1; "
                        "the smaller the SCORE, the higher the relevance; "
                        "a value of 2 is equivalent to no filtering; recommended value is around 0.5",
            ge=0.0,
            le=2.0,
        ),
        file_name: str = Body("", description="File name, supports SQL wildcards"),
        metadata: dict = Body({}, description="Filter by metadata, only supports top-level keys"),
) -> List[Dict]:
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    data = []
    if kb is not None:
        if query:
            docs = kb.search_docs(query, top_k, score_threshold)
            # data = [DocumentWithVSId(**x[0].dict(), score=x[1], id=x[0].metadata.get("id")) for x in docs]
            data = [DocumentWithVSId(**{"id": x.metadata.get("id"), **x.dict()}) for x in docs]
        elif file_name or metadata:
            data = kb.list_docs(file_name=file_name, metadata=metadata)
            for d in data:
                if "vector" in d.metadata:
                    del d.metadata["vector"]
    return [x.dict() for x in data]


def list_files(knowledge_base_name: str) -> ListResponse:
    if not validate_kb_name(knowledge_base_name):
        return ListResponse(code=403, msg="Don't attack me", data=[])

    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return ListResponse(
            code=404, msg=f"Knowledge base not found: {knowledge_base_name}", data=[]
        )
    else:
        all_docs = get_kb_file_details(knowledge_base_name)
        return ListResponse(data=all_docs)


def _save_files_in_thread(
        files: List[UploadFile], knowledge_base_name: str, override: bool
):
    """
    Save the uploaded files to the corresponding knowledge base directory using multiple threads.
    The generator returns the save result: {"code":200, "msg": "xxx", "data": {"knowledge_base_name":"xxx", "file_name": "xxx"}}
    """

    def save_file(file: UploadFile, knowledge_base_name: str, override: bool) -> dict:
        """
        Save a single file.
        """
        try:
            filename = file.filename
            file_path = get_file_path(
                knowledge_base_name=knowledge_base_name, doc_name=filename
            )
            data = {"knowledge_base_name": knowledge_base_name, "file_name": filename}

            file_content = file.file.read()  # read uploaded file content
            if (
                    os.path.isfile(file_path)
                    and not override
                    and os.path.getsize(file_path) == len(file_content)
            ):
                file_status = f"File {filename} already exists."
                logger.warn(file_status)
                return dict(code=404, msg=file_status, data=data)

            if not os.path.isdir(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "wb") as f:
                f.write(file_content)
            return dict(code=200, msg=f"Successfully uploaded file {filename}", data=data)
        except Exception as e:
            msg = f"Failed to upload file {filename}, error message: {e}"
            logger.error(f"{e.__class__.__name__}: {msg}")
            return dict(code=500, msg=msg, data=data)

    params = [
        {"file": file, "knowledge_base_name": knowledge_base_name, "override": override}
        for file in files
    ]
    for result in run_in_thread_pool(save_file, params=params):
        yield result


# def files2docs(files: List[UploadFile] = File(..., description="Upload files, supports multiple files"),
#                 knowledge_base_name: str = Form(..., description="Knowledge base name", examples=["samples"]),
#                 override: bool = Form(False, description="Override existing files"),
#                 save: bool = Form(True, description="Whether to save files to the knowledge base directory")):
#     def save_files(files, knowledge_base_name, override):
#         for result in _save_files_in_thread(files, knowledge_base_name=knowledge_base_name, override=override):
#             yield json.dumps(result, ensure_ascii=False)

#     def files_to_docs(files):
#         for result in files2docs_in_thread(files):
#             yield json.dumps(result, ensure_ascii=False)


def upload_docs(
        files: List[UploadFile] = File(..., description="Upload files, supports multiple files"),
        knowledge_base_name: str = Form(
            ..., description="Knowledge base name", examples=["samples"]
        ),
        override: bool = Form(False, description="Override existing files"),
        to_vector_store: bool = Form(True, description="Whether to vectorize after uploading the files"),
        chunk_size: int = Form(Settings.kb_settings.CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
        chunk_overlap: int = Form(Settings.kb_settings.OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
        zh_title_enhance: bool = Form(Settings.kb_settings.ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
        docs: str = Form("", description="Custom docs, needs to be a JSON string"),
        not_refresh_vs_cache: bool = Form(False, description="Do not save the vector store for now (used for FAISS)"),
) -> BaseResponse:
    """
    API endpoint: upload files, and/or vectorize them
    """
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")

    docs = json.loads(docs) if docs else {}
    failed_files = {}
    file_names = list(docs.keys())

    # First save the uploaded files to disk
    for result in _save_files_in_thread(
            files, knowledge_base_name=knowledge_base_name, override=override
    ):
        filename = result["data"]["file_name"]
        if result["code"] != 200:
            failed_files[filename] = result["msg"]

        if filename not in file_names:
            file_names.append(filename)

    # Vectorize the saved files
    if to_vector_store:
        result = update_docs(
            knowledge_base_name=knowledge_base_name,
            file_names=file_names,
            override_custom_docs=True,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            zh_title_enhance=zh_title_enhance,
            docs=docs,
            not_refresh_vs_cache=True,
        )
        failed_files.update(result.data["failed_files"])
        if not not_refresh_vs_cache:
            kb.save_vector_store()

    return BaseResponse(
        code=200, msg="File upload and vectorization complete", data={"failed_files": failed_files}
    )


def delete_docs(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        file_names: List[str] = Body(..., examples=[["file_name.md", "test.txt"]]),
        delete_content: bool = Body(False),
        not_refresh_vs_cache: bool = Body(False, description="Do not save the vector store for now (used for FAISS)"),
) -> BaseResponse:
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")

    failed_files = {}
    for file_name in file_names:
        if not kb.exist_doc(file_name):
            failed_files[file_name] = f"File not found: {file_name}"

        try:
            kb_file = KnowledgeFile(
                filename=file_name, knowledge_base_name=knowledge_base_name
            )
            kb.delete_doc(kb_file, delete_content, not_refresh_vs_cache=True)
        except Exception as e:
            msg = f"Failed to delete file {file_name}, error message: {e}"
            logger.error(f"{e.__class__.__name__}: {msg}")
            failed_files[file_name] = msg

    if not not_refresh_vs_cache:
        kb.save_vector_store()

    return BaseResponse(
        code=200, msg=f"File deletion complete", data={"failed_files": failed_files}
    )


def update_info(
        knowledge_base_name: str = Body(
            ..., description="Knowledge base name", examples=["samples"]
        ),
        kb_info: str = Body(..., description="Knowledge base description", examples=["This is a knowledge base"]),
):
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")
    kb.update_info(kb_info)

    return BaseResponse(code=200, msg=f"Knowledge base description updated", data={"kb_info": kb_info})


def update_docs(
        knowledge_base_name: str = Body(
            ..., description="Knowledge base name", examples=["samples"]
        ),
        file_names: List[str] = Body(
            ..., description="File names, supports multiple files", examples=[["file_name1", "text.txt"]]
        ),
        chunk_size: int = Body(Settings.kb_settings.CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
        chunk_overlap: int = Body(Settings.kb_settings.OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
        zh_title_enhance: bool = Body(Settings.kb_settings.ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
        override_custom_docs: bool = Body(False, description="Whether to override previously customized docs"),
        docs: str = Body("", description="Custom docs, needs to be a JSON string"),
        not_refresh_vs_cache: bool = Body(False, description="Do not save the vector store for now (used for FAISS)"),
) -> BaseResponse:
    """
    Update knowledge base documents
    """
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")

    failed_files = {}
    kb_files = []
    docs = json.loads(docs) if docs else {}

    # Generate the list of files that need to load docs
    for file_name in file_names:
        file_detail = get_file_detail(kb_name=knowledge_base_name, filename=file_name)
        # If the file previously used custom docs, decide whether to skip or override based on the parameter
        if file_detail.get("custom_docs") and not override_custom_docs:
            continue
        if file_name not in docs:
            try:
                kb_files.append(
                    KnowledgeFile(
                        filename=file_name, knowledge_base_name=knowledge_base_name
                    )
                )
            except Exception as e:
                msg = f"Error loading document {file_name}: {e}"
                logger.error(f"{e.__class__.__name__}: {msg}")
                failed_files[file_name] = msg

    # Generate docs from files and vectorize them.
    # This leverages KnowledgeFile's caching: load Documents in multiple threads and then pass them to KnowledgeFile
    for status, result in files2docs_in_thread(
            kb_files,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            zh_title_enhance=zh_title_enhance,
    ):
        if status:
            kb_name, file_name, new_docs = result
            kb_file = KnowledgeFile(
                filename=file_name, knowledge_base_name=knowledge_base_name
            )
            kb_file.splited_docs = new_docs
            kb.update_doc(kb_file, not_refresh_vs_cache=True)
        else:
            kb_name, file_name, error = result
            failed_files[file_name] = error

    # Vectorize the custom docs
    for file_name, v in docs.items():
        try:
            v = [x if isinstance(x, Document) else Document(**x) for x in v]
            kb_file = KnowledgeFile(
                filename=file_name, knowledge_base_name=knowledge_base_name
            )
            kb.update_doc(kb_file, docs=v, not_refresh_vs_cache=True)
        except Exception as e:
            msg = f"Error adding custom docs for {file_name}: {e}"
            logger.error(f"{e.__class__.__name__}: {msg}")
            failed_files[file_name] = msg

    if not not_refresh_vs_cache:
        kb.save_vector_store()

    return BaseResponse(
        code=200, msg=f"Document update complete", data={"failed_files": failed_files}
    )


def download_doc(
        knowledge_base_name: str = Query(
            ..., description="Knowledge base name", examples=["samples"]
        ),
        file_name: str = Query(..., description="File name", examples=["test.txt"]),
        preview: bool = Query(False, description="Yes: preview in browser; No: download"),
):
    """
    Download a knowledge base document
    """
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")

    if preview:
        content_disposition_type = "inline"
    else:
        content_disposition_type = None

    try:
        kb_file = KnowledgeFile(
            filename=file_name, knowledge_base_name=knowledge_base_name
        )

        if os.path.exists(kb_file.filepath):
            return FileResponse(
                path=kb_file.filepath,
                filename=kb_file.filename,
                media_type="multipart/form-data",
                content_disposition_type=content_disposition_type,
            )
    except Exception as e:
        msg = f"Failed to read file {kb_file.filename}, error message: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=500, msg=f"Failed to read file {kb_file.filename}")


def recreate_vector_store(
        knowledge_base_name: str = Body(..., examples=["samples"]),
        allow_empty_kb: bool = Body(True),
        vs_type: str = Body(Settings.kb_settings.DEFAULT_VS_TYPE, description="Specify the vector store type for an empty knowledge base. Existing knowledge bases use their original vector store type by default."),
        embed_model: str = Body(get_default_embedding(), description="Specify the embedding model for an empty knowledge base. Existing knowledge bases use their original embedding model by default."),
        chunk_size: int = Body(Settings.kb_settings.CHUNK_SIZE, description="Maximum length of a single text segment in the knowledge base"),
        chunk_overlap: int = Body(Settings.kb_settings.OVERLAP_SIZE, description="Overlap length between adjacent text segments in the knowledge base"),
        zh_title_enhance: bool = Body(Settings.kb_settings.ZH_TITLE_ENHANCE, description="Whether to enable Chinese title enhancement"),
        not_refresh_vs_cache: bool = Body(False, description="Do not save the vector store for now (used for FAISS)"),
):
    """
    recreate vector store from the content.
    this is usefull when user can copy files to content folder directly instead of upload through network.
    by default, get_service_by_name only return knowledge base in the info.db and having document files in it.
    set allow_empty_kb to True make it applied on empty knowledge base which it not in the info.db or having no documents.
    """

    def output():
        try:
            kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
            if kb is None:
                kb = KBServiceFactory.get_service(knowledge_base_name, vs_type, embed_model)
            if not kb.exists() and not allow_empty_kb:
                yield {"code": 404, "msg": f"Knowledge base '{knowledge_base_name}' not found"}
            else:
                ok, msg = kb.check_embed_model()
                if not ok:
                    yield {"code": 404, "msg": msg}
                else:
                    if kb.exists():
                        kb.clear_vs()
                    kb.create_kb()
                    files = list_files_from_folder(knowledge_base_name)
                    kb_files = [(file, knowledge_base_name) for file in files]
                    i = 0
                    for status, result in files2docs_in_thread(
                            kb_files,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            zh_title_enhance=zh_title_enhance,
                    ):
                        if status:
                            kb_name, file_name, docs = result
                            kb_file = KnowledgeFile(
                                filename=file_name, knowledge_base_name=kb_name
                            )
                            kb_file.splited_docs = docs
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
                            kb.add_doc(kb_file, not_refresh_vs_cache=True)
                        else:
                            kb_name, file_name, error = result
                            msg = f"Error adding file '{file_name}' to knowledge base '{knowledge_base_name}': {error}. Skipped."
                            logger.error(msg)
                            yield json.dumps(
                                {
                                    "code": 500,
                                    "msg": msg,
                                }
                            )
                        i += 1
                    if not not_refresh_vs_cache:
                        kb.save_vector_store()
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return

    return EventSourceResponse(output())
