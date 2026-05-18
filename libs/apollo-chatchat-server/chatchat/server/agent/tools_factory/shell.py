# LangChain's Shell tool
from langchain_community.tools import ShellTool

from chatchat.server.pydantic_v1 import Field

from .tools_registry import regist_tool

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)

@regist_tool(title="System Command")
def shell(query: str = Field(description="The command to execute")):
    """Use Shell to execute system shell commands"""
    tool = ShellTool()
    return BaseToolOutput(tool.run(tool_input=query))
