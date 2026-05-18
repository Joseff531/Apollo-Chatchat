from typing import Literal

from fastapi import APIRouter, Body

from chatchat.server.types.server.response.base import BaseResponse
from chatchat.settings import Settings
from chatchat.server.utils import get_prompt_template, get_server_configs

server_router = APIRouter(prefix="/server", tags=["Server State"])

available_template_types = list(Settings.prompt_settings.model_fields.keys())

# Server-related endpoints
server_router.post(
    "/configs",
    summary="Get the server's raw configuration information",
)(get_server_configs)


@server_router.post("/get_prompt_template", summary="Get the prompt template configured on the server", response_model=BaseResponse)
def get_server_prompt_template(
        type: str = Body(
            "llm_model", description="Template type. Available values: {available_template_types}"
        ),
        name: str = Body("default", description="Template name"),
):
    prompt_template = get_prompt_template(type=type, name=name)
    if prompt_template is None:
        return BaseResponse.error("Prompt template not found")
    return BaseResponse.success(prompt_template)
