import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Union

from langchain.prompts.chat import ChatMessagePromptTemplate

from chatchat.server.pydantic_v2 import BaseModel, Field
from chatchat.utils import build_logger


logger = build_logger()


class History(BaseModel):
    """
    Conversation history.
    Can be created from a dict, e.g.
    h = History(**{"role":"user","content":"hello"})
    Can also be converted to a tuple, e.g.
    h.to_msy_tuple = ("human", "hello")
    """

    role: str = Field(...)
    content: str = Field(...)

    def to_msg_tuple(self):
        return "ai" if self.role == "assistant" else "human", self.content

    def to_msg_template(self, is_raw=True) -> ChatMessagePromptTemplate:
        role_maps = {
            "ai": "assistant",
            "human": "user",
        }
        role = role_maps.get(self.role, self.role)
        if is_raw:  # By default, historical messages are plain text without input variables.
            content = "{% raw %}" + self.content + "{% endraw %}"
        else:
            content = self.content

        return ChatMessagePromptTemplate.from_template(
            content,
            "jinja2",
            role=role,
        )

    @classmethod
    def from_data(cls, h: Union[List, Tuple, Dict]) -> "History":
        if isinstance(h, (list, tuple)) and len(h) >= 2:
            h = cls(role=h[0], content=h[1])
        elif isinstance(h, dict):
            h = cls(**h)

        return h
