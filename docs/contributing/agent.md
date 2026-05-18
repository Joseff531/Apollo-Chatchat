# Agent and Function Call

If you are looking for the Agent portion of this framework, please refer to `libs/apollo-chatchat-server/chatchat/server/agent`, which contains all the Agent-related code in the current framework.

## Agent Factory

The Agent Factory stores specialized Agent models. Currently, it includes two series:

+ GLM series: includes the GLM-3 and GLM-4 open-source models.
+ Qwen series: supports the Qwen-2 and Qwen1.5 open-source models.

## Tool Factory

The Tool Factory stores specialized tools. Chatchat currently ships with several built-in tools:

+ Amap POI Search Tool: uses the Amap API to perform POI searches, returning related place information based on a given location and category.
+ Amap Weather Query Tool: uses the Amap API to fetch weather information for a given city.
+ Audio Q&A Tool: handles audio questions, using the provided audio file and text question to generate an answer.
+ ARXIV Paper Tool: uses Arxiv.org to search and retrieve scientific papers across various fields.
+ Math Calculator Tool: performs simple math calculations by converting the user's question into a math expression evaluable by numexpr.
+ Internet Search Tool: uses a specified search engine to search the internet for information.
+ Local Knowledge Base Tool: searches the local knowledge base, retrieving information based on the specified database and query.
+ YouTube Video Tool: uses this tool to search for YouTube videos.
+ System Command Tool: executes system commands via the shell.
+ Text-to-Image Tool: generates images based on the user's description.
+ Prometheus Dialogue Tool: converts natural language into PromQL and executes queries on a Prometheus server, returning the results.
+ Database Dialogue Tool: converts natural language into SQL and executes queries against a database, returning the results.
+ Image Dialogue Tool: generates answers based on an image and a text question, and draws rectangles on the image.
+ Weather Query Tool: queries the current weather conditions for a given city.
+ Wikipedia Search Tool: performs searches using Wikipedia.
+ WolframAlpha Tool: computes complex formulas and performs advanced mathematical operations.

## Adding Your Own Tool

We support adding your own tools in a LangChain-compatible way. You can refer to the tool templates in
`libs/apollo-chatchat-server/chatchat/server/agent/tools_registry` to add your own tools.
A simple construction approach is:

1. Create a new `.py` file to implement your tool, for example:

```python
@regist_tool(title="Math Calculator")
def calculate(text: str = Field(description="a math expression")) -> float:
    """
    Useful to answer questions about simple calculations.
    translate user question to a math expression that can be evaluated by numexpr.
    """
    import numexpr

    try:
        ret = str(numexpr.evaluate(text))
    except Exception as e:
        ret = f"wrong: {e}"

    return BaseToolOutput(ret)
```

+ Use the `@regist_tool` decorator to register the tool.
+ Specify the parameters to be passed in and the function corresponding to those parameters.
+ Use `BaseToolOutput` to wrap the tool's output.

2. If you would like to use a tool provided by LangChain, you can do so as follows. Here is an example using the LangChain Shell tool:

```python
from langchain_community.tools import ShellTool
from chatchat.server.pydantic_v1 import Field
from .tools_registry import BaseToolOutput, regist_tool


@regist_tool(title="System Command")
def shell(query: str = Field(description="The command to execute")):
    """Use Shell to execute system shell commands"""
    tool = ShellTool()
    return BaseToolOutput(tool.run(tool_input=query))
```

This example instantiates a tool based on the LangChain tool and exposes it as a callable Chatchat tool.

## Letting the Model Know to Call a Tool

In addition to adding tools, when the user provides a prompt, emphasize as much as possible that a tool is needed. This increases the probability that the model will invoke the tool. For example:

#### search_internet

Use this tool because the user needs to perform an online search. These are typically questions you do not know, with characteristics
such as:

+ Search the web and tell me xxx
+ I want to know the latest news
  Or the user clearly intends to obtain factual information.
  The return field is as follows:

```
search_internet
```

#### search_local_knowledge

Use this tool when the user needs to retrieve local knowledge. This knowledge is typically domain-specific information that your own capabilities lack, or it relates to a task the user has explicitly specified.
Examples:

+ Tell me the xxx of xxx
+ What is the xxx of xxx in xxx
  The return field is as follows:

```
search_local_knowledge
```

## Tuning the Agent System Prompt

If your model is not compatible with LangChain's default Struct Agent prompt template, you can customize the prompt in the configuration file `prompt_settings.yaml`.
For example, the prompt for the GLM-3 model is:

```
You can answer using the tools.Respond to the human as helpfully and
accurately as possible.\nYou have access to the following tools:\n{tools}\nUse
a json blob to specify a tool by providing an action key (tool name)\nand an action_input
key (tool input).\nValid \"action\" values: \"Final Answer\" or  [{tool_names}]\n
Provide only ONE action per $JSON_BLOB, as shown:\n\n```\n{{{{\n  \"action\":
$TOOL_NAME,\n  \"action_input\": $INPUT\n}}}}\n```\n\nFollow this format:\n\n
Question: input question to answer\nThought: consider previous and subsequent
steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat
Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n\
```\n{{{{\n  \"action\": \"Final Answer\",\n  \"action_input\": \"Final response
to human\"\n}}}}\nBegin! Reminder to ALWAYS respond with a valid json blob of
a single action. Use tools if necessary.\nRespond directly if appropriate. Format
is Action:```$JSON_BLOB```then Observation:.\nQuestion: {input}\n\n{agent_scratchpad}\n
```

Additionally, if your model's return format is incompatible with LangChain's default Struct Agent, you will need to customize the Agent execution logic just like GLM-3 / GLM-4 do, to ensure the Function Call content is returned correctly.
