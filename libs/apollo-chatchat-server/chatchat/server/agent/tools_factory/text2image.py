import base64
from datetime import datetime
import os
import uuid
from typing import List, Literal

import openai
from PIL import Image

from chatchat.settings import Settings
from chatchat.server.pydantic_v1 import Field
from chatchat.server.utils import MsgType, get_tool_config, get_model_info

from .tools_registry import regist_tool

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)

@regist_tool(title="""
# Text-to-Image Generation Tool
## Description
Generates an image from the user's description.
## Request Parameters
Name    Type    Required    Description
prompt  String  Yes         Text description of the desired image
size    String  No          Image size. Allowed values: 1024x1024, 768x1344, 864x1152, 1344x768, 1152x864, 1440x720, 720x1440. Defaults to 1024x1024.
""", return_direct=True)
def text2images(
    prompt: str = Field(description="The user's description"),
    n: int = Field(1, description="Number of images to generate"),
    size: Literal["1024x1024", "768x1344", "864x1152", "1344x768", "1152x864", "1440x720", "720x1440"] = Field(description="Image size"),
):
    """Generate an image from the user's description."""

    tool_config = get_tool_config("text2images")
    model_config = get_model_info(tool_config["model"])
    assert model_config, "Please configure the text-to-image model correctly."

    client = openai.Client(
        base_url=model_config["api_base_url"],
        api_key=model_config["api_key"],
        timeout=600,
    )
    resp = client.images.generate(
        prompt=prompt,
        n=n,
        size=size,
        response_format="b64_json",
        model=model_config["model_name"],
    )
    images = []
    for x in resp.data:
        if x.b64_json is not None:
            uid = uuid.uuid4().hex
            today = datetime.now().strftime("%Y-%m-%d")
            path = os.path.join(Settings.basic_settings.MEDIA_PATH, "image", today)
            os.makedirs(path, exist_ok=True)
            filename = f"image/{today}/{uid}.png"
            with open(os.path.join(Settings.basic_settings.MEDIA_PATH, filename), "wb") as fp:
                fp.write(base64.b64decode(x.b64_json))
            images.append(filename)
        else:
            images.append(x.url)
    return BaseToolOutput(
        {"message_type": MsgType.IMAGE, "images": images}, format="json"
    )


if __name__ == "__main__":
    import sys
    from io import BytesIO
    from pathlib import Path

    from matplotlib import pyplot as plt

    sys.path.append(str(Path(__file__).parent.parent.parent.parent))

    prompt = "draw a house with trees and river"
    prompt = "Draw a mountain cabin with trees, grass and a river."
    params = text2images.args_schema.parse_obj({"prompt": prompt}).dict()
    print(params)
    image = text2images.invoke(params)[0]
    buffer = BytesIO(base64.b64decode(image))
    image = Image.open(buffer)
    plt.imshow(image)
    plt.show()
