from pydantic import Field, BaseModel


class CallToolParam(BaseModel):
    name: str = Field(..., description="Tool name")
    tool_input: dict = Field({}, description="Knowledge base information"),
