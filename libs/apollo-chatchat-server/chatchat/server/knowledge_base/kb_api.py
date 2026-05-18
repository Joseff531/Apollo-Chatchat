import urllib

from fastapi import Body

from chatchat.settings import Settings
from chatchat.server.db.repository.knowledge_base_repository import list_kbs_from_db
from chatchat.server.knowledge_base.kb_service.base import KBServiceFactory
from chatchat.server.knowledge_base.utils import validate_kb_name
from chatchat.server.utils import BaseResponse, ListResponse, get_default_embedding
from chatchat.utils import build_logger


logger = build_logger()


def list_kbs():
    # Get List of Knowledge Base
    return ListResponse(data=list_kbs_from_db())


def create_kb(
    knowledge_base_name: str = Body(..., examples=["samples"]),
    vector_store_type: str = Body(Settings.kb_settings.DEFAULT_VS_TYPE),
    kb_info: str = Body("", description="Knowledge base description, used by the Agent to select a knowledge base."),
    embed_model: str = Body(get_default_embedding()),
) -> BaseResponse:
    # Create selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return BaseResponse(code=404, msg="Knowledge base name cannot be empty, please re-enter the knowledge base name")

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is not None:
        return BaseResponse(code=404, msg=f"A knowledge base with the same name already exists: {knowledge_base_name}")

    kb = KBServiceFactory.get_service(
        knowledge_base_name, vector_store_type, embed_model, kb_info=kb_info
    )
    try:
        kb.create_kb()
    except Exception as e:
        msg = f"Error creating knowledge base: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=200, msg=f"Knowledge base {knowledge_base_name} has been added")


def delete_kb(
    knowledge_base_name: str = Body(..., examples=["samples"]),
) -> BaseResponse:
    # Delete selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)

    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)

    if kb is None:
        return BaseResponse(code=404, msg=f"Knowledge base not found: {knowledge_base_name}")

    try:
        status = kb.clear_vs()
        status = kb.drop_kb()
        if status:
            return BaseResponse(code=200, msg=f"Successfully deleted knowledge base {knowledge_base_name}")
    except Exception as e:
        msg = f"Unexpected error while deleting knowledge base: {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=500, msg=f"Failed to delete knowledge base {knowledge_base_name}")
