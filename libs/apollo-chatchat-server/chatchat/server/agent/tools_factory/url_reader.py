"""
Use the jina-ai/reader project to turn URL contents into a text form that is easy for an LLM to understand.
"""
import requests

import re

from chatchat.server.pydantic_v1 import Field
from chatchat.server.utils import get_tool_config

from chatchat.server.agent.tools_factory.tools_registry import format_context

from .tools_registry import regist_tool

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)

@regist_tool(title="URL Content Reader")
def url_reader(
        url: str = Field(
            description="The URL to be processed, so that its web content can be made more clear to read. Then provide a detailed description of the content in about 500 words. As structured as possible. ONLY THE LINK SHOULD BE PASSED IN."),
):
    """Use this tool to get the clear content of a URL."""

    tool_config = get_tool_config("url_reader")
    timeout = tool_config.get("timeout")

    # Extract the URL part from the input text. The input may be a full sentence.
    url_pattern = r'http[s]?://[a-zA-Z0-9./?&=_%#-]+'
    match = re.search(url_pattern, url)
    url = match.group(0) if match else None

    if url is None:
        return BaseToolOutput({"error": "No URL"})

    reader_url = "https://r.jina.ai/{url}".format(url=url)

    response = requests.get(reader_url, timeout=timeout)

    if response.status_code == 200:
        return BaseToolOutput(
            {"result": response.text, "docs": [{"page_content": response.text, "metadata": {'source': url, 'id': ''}}]},
            format=format_context)
    else:
        return BaseToolOutput({"error": "Timeout"})
