import asyncio
from typing import AsyncIterable, Optional

from fastapi import Body
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from sse_starlette.sse import EventSourceResponse

from chatchat.server.utils import get_OpenAI, get_prompt_template, wrap_done, build_logger


logger = build_logger()


async def completion(
    query: str = Body(..., description="User input", examples=["enraged and humiliated"]),
    stream: bool = Body(False, description="Stream output"),
    echo: bool = Body(False, description="In addition to the output, also echo the input"),
    model_name: str = Body(None, description="LLM model name."),
    temperature: float = Body(0.01, description="LLM sampling temperature", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        1024, description="Cap on the number of tokens the LLM can generate; the default None means use the model's maximum"
    ),
    # top_p: float = Body(TOP_P, description="LLM nucleus sampling. Do not set together with temperature", gt=0.0, lt=1.0),
    prompt_name: str = Body(
        "default", description="Name of the prompt template to use (configured in configs/prompt_config.py)"
    ),
):
    # TODO: ApiModelWorker handles requests as chat by default and parses params["prompt"] into messages, so ApiModelWorker usage needs corresponding handling
    async def completion_iterator(
        query: str,
        model_name: str = None,
        prompt_name: str = prompt_name,
        echo: bool = echo,
    ) -> AsyncIterable[str]:
        try:
            nonlocal max_tokens
            callback = AsyncIteratorCallbackHandler()
            if isinstance(max_tokens, int) and max_tokens <= 0:
                max_tokens = None

            model = get_OpenAI(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                callbacks=[callback],
                echo=echo,
                local_wrap=True,
            )

            prompt_template = get_prompt_template("llm_model", prompt_name)
            prompt = PromptTemplate.from_template(prompt_template, template_format="jinja2")
            chain = LLMChain(prompt=prompt, llm=model)

            # Begin a task that runs in the background.
            task = asyncio.create_task(
                wrap_done(chain.acall({"input": query}), callback.done),
            )

            if stream:
                async for token in callback.aiter():
                    # Use server-sent-events to stream the response
                    yield token
            else:
                answer = ""
                async for token in callback.aiter():
                    answer += token
                yield answer

            await task
        except asyncio.exceptions.CancelledError:
            logger.warning("streaming progress has been interrupted by user.")
            return

    return EventSourceResponse(
        completion_iterator(
            query=query, model_name=model_name, prompt_name=prompt_name
        ),
    )
