## Common API Endpoint Usage

### Overview

All endpoints' parameters can be viewed and tested at `{api_address}/docs`.

### /tools

This endpoint lists all tools along with their parameter information.  
Input parameters: none  
Example output:
```
{
  "code": 200,
  "msg": "success",
  "data": {
    "search_local_knowledgebase": {
      "name": "search_local_knowledgebase",
      "title": "Local Knowledge Base",
      "description": "Use local knowledgebase from one or more of these: test: knowledge base about test samples: knowledge base answering questions about this project's issues to get information. Only local data on this knowledge use this tool. The 'database' should be one of the above [test samples].",
      "args": {
        "database": {
          "title": "Database",
          "description": "Database for Knowledge Search",
          "choices": [
            "test",
            "samples"
          ],
          "type": "string"
        },
        "query": {
          "title": "Query",
          "description": "Query for Knowledge Search",
          "type": "string"
        }
      },
      "config": {
        "use": false,
        "top_k": 3,
        "score_threshold": 1,
        "conclude_prompt": {
          "with_result": "<instruction>Answer the question concisely and professionally based on the known information. If the answer cannot be derived from it, please say \"The question cannot be answered based on the known information\". Do not add fabricated content to the answer. Please answer in English. </instruction>\n<known information>{{ context }}</known information>\n<question>{{ question }}</question>\n",
          "without_result": "Please answer my question based on my prompt:\n{{ question }}\nNote that you must emphasize at the end of your answer that your reply is based on your own experience and not on reference materials.\n"
        }
      }
    },
    ...
  }
}
```

### General Chat Endpoint (/chat/chat/completions)

The primary chat endpoint, compatible with the openai sdk format. It supports the following three chat modes:  
- Pure LLM chat. Simply pass `model` and `messages`; optional parameters include `temperature`, `max_tokens`, `stream`, etc.
- Agent chat. On top of the LLM chat, pass the `tools` parameter so the LLM can select appropriate tools and parameters as reference for the conversation.
- Semi-Agent chat. On top of the LLM chat, pass the `tool_choice` parameter so the LLM parses parameters and directly invokes the specified tool as reference for the conversation. If the LLM's parameter parsing is not ideal, you may also specify the tool parameters manually.

Input parameters: consistent with the openai sdk parameters. The following optimizations have been made for chatchat:  
- The `tools` parameter can use the tool names defined in chatchat; all supported tools can be retrieved via the `/tools` endpoint.
- When `tool_choice` is specified, you can pass `tool_input={...}` in `extra_body` to manually specify tool parameters.
- When using the Agent feature, the `stream` parameter must be set to `True`. Because the Agent executes step by step, each step must be emitted one by one via SSE. Note: in this case the SSE unit is an execution step, and the LLM output is non-streaming.

Example calls:
- Pure LLM chat:
    ```python3
    base_url = "http://127.0.0.1:7861/chat"
    data = {
        "model": "qwen1.5-chat",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello, I am an AI large language model"},
            {"role": "user", "content": "Please introduce yourself in about 100 words"},
        ],
        "stream": True,
        "temperature": 0.7,
    }

    # Option 1: using requests
    import requests
    response = requests.post(f"{base_url}/chat/completions", json=data, stream=True)
    for line in response.iter_content(None, decode_unicode=True):
        print(line, end="", flush=True)

    # Option 2: using openai sdk
    import openai
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    resp = client.chat.completions.create(**data)
    for r in resp:
        print(r)
    ```

    ```shell
    # Output for option 1, SSE format
    data: {"id":"chat6aa251c3-3425-11ef-be81-603a7c6af450","choices":[{"delta":{"content":"","function_call":null,"role":"assistant","tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719452077,"model":"qwen1.5-chat","object":"chat.completion.chunk","system_fingerprint":null,"usage":null,"message_id":null,"status":null}
    data: {"id":"chat6aa251c3-3425-11ef-be81-603a7c6af450","choices":[{"delta":{"content":"I am","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719452077,"model":"qwen1.5-chat","object":"chat.completion.chunk","system_fingerprint":null,"usage":null,"message_id":null,"status":null}
    data: {"id":"chat6abf605c-3425-11ef-9f15-603a7c6af450","choices":[{"delta":{"content":"Alibaba Cloud","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719452078,"model":"qwen1.5-chat","object":"chat.completion.chunk","system_fingerprint":null,"usage":null,"message_id":null,"status":null}
    data: {"id":"chat6ad00242-3425-11ef-af45-603a7c6af450","choices":[{"delta":{"content":"a proprietary","function_call":null,"role":null,"tool_calls":null},"finish_reason":null,"index":0,"logprobs":null}],"created":1719452078,"model":"qwen1.5-chat","object":"chat.completion.chunk","system_fingerprint":null,"usage":null,"message_id":null,"status":null}
    ...
    ```
    ```shell
    # Output for option 2:
    ChatCompletionChunk(id='chat682070c8-3426-11ef-947d-603a7c6af450', choices=[Choice(delta=ChoiceDelta(content='', function_call=None, role='assistant', tool_calls=None), finish_reason=None, index=0, logprobs=None)], created=1719452503, model='qwen1.5-chat', object='chat.completion.chunk', system_fingerprint=None, usage=None, message_id=None, status=None)
    ChatCompletionChunk(id='chat682070c8-3426-11ef-947d-603a7c6af450', choices=[Choice(delta=ChoiceDelta(content='I am', function_call=None, role=None, tool_calls=None), finish_reason=None, index=0, logprobs=None)], created=1719452503, model='qwen1.5-chat', object='chat.completion.chunk', system_fingerprint=None, usage=None, message_id=None, status=None)
    ChatCompletionChunk(id='chat683fdd72-3426-11ef-be33-603a7c6af450', choices=[Choice(delta=ChoiceDelta(content='developed by Alibaba', function_call=None, role=None, tool_calls=None), finish_reason=None, index=0, logprobs=None)], created=1719452503, model='qwen1.5-chat', object='chat.completion.chunk', system_fingerprint=None, usage=None, message_id=None, status=None)
    ChatCompletionChunk(id='chat68511ba1-3426-11ef-b2be-603a7c6af450', choices=[Choice(delta=ChoiceDelta(content='Cloud R&D', function_call=None, role=None, tool_calls=None), finish_reason=None, index=0, logprobs=None)], created=1719452503, model='qwen1.5-chat', object='chat.completion.chunk', system_fingerprint=None, usage=None, message_id=None, status=None)
    ...
    ```
- Agent chat  
    The following example only demonstrates the `requests` approach. You can try the `openai sdk` yourself; the parameters and output are the same.
    ```python3
    base_url = "http://127.0.0.1:7861/chat"
    tools = list(requests.get(f"http://127.0.0.1:7861/tools").json()["data"])
    data = {
        "model": "qwen1.5-chat",
        "messages": [
            {"role": "user", "content": "37+48=?"},
        ],
        "stream": True,
        "temperature": 0.7,
        "tools": tools,
    }

    import requests
    response = requests.post(f"{base_url}/chat/completions", json=data, stream=True)
    for line in response.iter_content(None, decode_unicode=True):
        print(line)
    ```
    ```shell
    # Output:
    data: {"id": "chat39830df6-d016-4b91-b502-e113bb71542c", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453364, "status": 1, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "", "tool_calls": []}, "role": "assistant"}]}
    data: {"id": "chatb05f9cb2-1e93-4657-806b-29ec135483b9", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453367, "status": 3, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "Thought: The problem involves adding two numbers: 37 and 48. To perform this calculation, I will use the calculator API.\nAction: calculate\nAction Input: {\"text\": \"37 + 48\"}", "tool_calls": []}, "role": "assistant"}]}
    data: {"id": "chat73adade0-b62f-412a-a448-9002a59cbc30", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453367, "status": 4, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "Thought: The problem involves adding two numbers: 37 and 48. To perform this calculation, I will use the calculator API.\nAction: calculate\nAction Input: {\"text\": \"37 + 48\"}", "tool_calls": []}, "role": "assistant"}]}
    data: {"id": "chat7752232b-7360-4010-bc55-e50fa8ac9f44", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453367, "status": 6, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "", "tool_calls": [{"index": 0, "id": "f2b20744-3958-4e3b-9e51-c5738d87a020", "type": "function", "function": {"name": "calculate", "arguments": "{'text': '37 + 48'}"}, "tool_output": null, "is_error": false}]}, "role": "assistant"}]}
    data: {"id": "chatef5f948e-4772-477d-823d-ce74b38ba586", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453367, "status": 7, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "", "tool_calls": [{"index": 0, "id": "f2b20744-3958-4e3b-9e51-c5738d87a020", "type": "function", "function": {"name": "calculate", "arguments": "{'text': '37 + 48'}"}, "tool_output": "85", "is_error": false}]}, "role": "assistant"}]}
    data: {"id": "chatdee106c6-42e6-41cf-b2df-692431829e4d", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453367, "status": 1, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": "", "tool_calls": []}, "role": "assistant"}]}
    data: {"id": "chat819ef11b-576f-4489-b6bb-47565eb69ee8", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453370, "status": 3, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": " The calculation 37 + 48 has been successfully performed using the calculate API, resulting in the result of 85. Therefore, the final answer to the given question is 85. \n\nJSON Object:\n{\n  \"answer\": 85\n}", "tool_calls": []}, "role": "assistant"}]}
    data: {"id": "chatb6b1071b-5346-4713-922c-b2887728491f", "object": "chat.completion.chunk", "model": "qwen1.5-chat", "created": 1719453370, "status": 5, "message_type": 1, "message_id": null, "is_ref": false, "choices": [{"delta": {"content": " The calculation 37 + 48 has been successfully performed using the calculate API, resulting in the result of 85. Therefore, the final answer to the given question is 85. \n\nJSON Object:\n{\n  \"answer\": 85\n}", "tool_calls": []}, "role": "assistant"}]}
    ```
    The output contains a `status` field representing the Agent's current execution stage. In outputs where `status` is 6 or 7, you can see tool_call information. The specific values are:
    ```python3
    class AgentStatus:
        llm_start: int = 1
        llm_new_token: int = 2
        llm_end: int = 3
        agent_action: int = 4
        agent_finish: int = 5
        tool_start: int = 6
        tool_end: int = 7
        error: int = 8
    ```

    The output also contains a `message_type` field representing the type of output content, mainly used by the frontend to render different messages. Currently, only the `text2image` tool returns `IMAGE`; all others return `TEXT`. The specific values are:
    ```python3
    class MsgType:
        TEXT = 1
        IMAGE = 2
        AUDIO = 3
        VIDEO = 4
    ```
- Knowledge base chat (LLM auto-parses parameters)  
    Simply specify `tool_choice` as `"search_local_knowledgebase"` to use the knowledge base chat feature. Other tool-based chats work similarly.
    ```python3
    base_url = "http://127.0.0.1:7861/chat"
    data = {
        "messages": [
            {"role": "user", "content": "How do I ask questions to get high-quality answers"},
        ],
        "model": "qwen1.5-chat",
        "tool_choice": "search_local_knowledgebase",
        "stream": True,
    }

    import requests
    response = requests.post(f"{base_url}/chat/completions", json=data, stream=True)
    for line in response.iter_content(None, decode_unicode=True):
        print(line)
    ```
    In the responses where `status` is 6 or 7, you can obtain the tool's invocation and output information.  
    Because the output is lengthy, it is not shown here. Please try it yourself.
- Knowledge base chat (manually passed parameters)  
    Specify `tool_choice` as `"search_local_knowledgebase"` and set the tool parameters via `tool_input` to manually invoke the tool, allowing chat against a specific knowledge base.
    ```python3
    base_url = "http://127.0.0.1:7861/chat"
    data = {
        "messages": [
            {"role": "user", "content": "How do I ask questions to get high-quality answers"},
        ],
        "model": "qwen1.5-chat",
        "tool_choice": "search_local_knowledgebase",
        "tool_input": {"database": "samples", "query": "How do I ask questions to get high-quality answers"},
        "stream": True,
    }

    import requests
    response = requests.post(f"{base_url}/chat/completions", json=data, stream=True)
    for line in response.iter_content(None, decode_unicode=True):
        print(line)
    ```
    From the output, you can see that the tool-parsing steps where `status` is 6 or 7 are no longer present, indicating that the tool invocation was not performed by the LLM.  
    Because the output is lengthy, it is not shown here. Please try it yourself.


### RAG Endpoint (/knowledge_base/chat/compleitons)
Compared with the /chat/chat/completions endpoint, this endpoint is primarily used for RAG. It supports more parameters, and its return value is also openai sdk compatible. In addition to the parameters defined by openai.chat.completions, it also supports the following parameters:  
- mode: retrieval mode:
  - "local_kb": retrieve from a local knowledge base; provide "kb_name" to specify the knowledge base name
  - "temp_kb": file-based chat; provide "knowledge_id" to specify the temporary knowledge base ID for file chat
  - "search_engine": use a search engine; provide "search_engine_name" to specify the search engine to use
- top_k: number of retrieval results
- score_threshold: matching score threshold
- prompt_name: name of the prompt template to use
- return_direct: if True, only the retrieval results are returned without going through the LLM
- messages: messages[-1]["content"] is used as the retrieval target; messages[:-1] is used as history

Return value:

- When stream is True, the first ChatCompletionChunk.docs contains the retrieval results
- When stream is False, ChatCompletion.docs contains the retrieval results


Example calls (using openai sdk to demonstrate local knowledge base Q&A; the requests-based parameters are the same, just place the content of extra_body directly into data):

- Local knowledge base Q&A
    ```python3
    base_url = "http://127.0.0.1:7861/knowledge_base/local_kb/samples"
    data = {
        "model": "qwen2-instruct",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello, I am an AI large language model"},
            {"role": "assistant", "content": "How do I ask high-quality questions?"},
        ],
        "stream": True,
        "temperature": 0.7,
        "extra_body": {
          "top_k": 3,
          "score_threshold": 2.0,
          "return_direct": True,
        },
    }

    import openai
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    resp = client.chat.completions.create(**data)
    for r in resp:
        print(r)
    ```

    Example output:
    ```shell
    ChatCompletionChunk(id='chat9973e445-8581-45ca-bde5-148fc724b30b', choices=[Choice(delta=None, finish_reason=None, index=None, logprobs=None, message={'role': 'assistant', 'content': '', 'finish_reason': 'stop', 'tool_calls': []})], created=1720592802, model=None, object='chat.completion', service_tier=None, system_fingerprint=None, usage=None, status=None, message_type=1, message_id=None, is_ref=False, docs=['Source [1] [test_files/test.txt](http://127.0.0.1:7861//knowledge_base/download_doc?knowledge_base_name=samples&file_name=test_files%2Ftest.txt) \n\n[This is that famous painting]: http://yesaiwen.com/art\nof\nasking\nchatgpt\nfor\nhigh\nquality\nansw\nengineering\ntechniques/#i\n3\t"The Art of Asking ChatGPT for High-Quality Answers"\n\n', 'Source [2] [test_files/test.txt](http://127.0.0.1:7861//knowledge_base/download_doc?knowledge_base_name=samples&file_name=test_files%2Ftest.txt) \n\nChatGPT is a large language model developed by OpenAI that can provide information on a wide range of topics.\n# How to Ask ChatGPT Questions to Get High-Quality Answers: A Complete Guide to Prompt Engineering Techniques\n## Introduction\nI am pleased to welcome you to my latest book, "The Art of Asking ChatGPT for High-Quality Answers: A complete Guide to Prompt Engineering Techniques". This book is a comprehensive guide that introduces various prompting techniques for generating high-quality answers from ChatGPT.\nWe will explore how to use different prompt engineering techniques to achieve different goals. ChatGPT is a state-of-the-art language model capable of producing human-like text. However, understanding how to correctly ask ChatGPT questions to get the high-quality output we need is essential, and that is precisely the purpose of this book.\nWhether you are an ordinary person, a researcher, a developer, or someone simply wishing to use ChatGPT as a personal assistant in your own field, this book is written for you. I use simple, easy-to-understand language, provide practical explanations, and include examples and prompt formulas for each technique. Through this book, you will learn how to use prompt engineering techniques to control ChatGPT\'s output and generate text that meets your specific needs.\nThroughout the book, we also provide examples of how to combine different prompting techniques to achieve more specific results. I hope you enjoy reading this book and gain knowledge from it as much as I enjoyed writing it.\n<div style="page\nbreak\nafter:always;"></div>\n## Chapter 1: Introduction to Prompt Engineering Techniques\nWhat is Prompt Engineering?\nPrompt engineering is the process of creating prompts or instructions that guide the output of a language model like ChatGPT. It allows users to control the model\'s output and generate text that meets their specific needs.\n\n', 'Source [3] [test_files/test.txt](http://127.0.0.1:7861//knowledge_base/download_doc?knowledge_base_name=samples&file_name=test_files%2Ftest.txt) \n\nA prompt formula is a specific format for prompts, typically composed of three main elements:\nTask: a clear and concise statement of what the prompt asks the model to generate.\nInstruction: instructions the model should follow when generating text.\nRole: the role the model should play when generating text.\nIn this book, we will explore various Prompt engineering techniques available for ChatGPT. We will discuss different types of prompts and how to use them to achieve the specific goals you want.\n<div style="page\nbreak\nafter:always;"></div>\n## Chapter 2: Instruction Prompting Techniques\nNow, let us begin exploring "instruction prompting techniques" and how to use them to generate high-quality text from ChatGPT.\nThe instruction prompting technique is a method of guiding ChatGPT\'s output by providing the model with specific instructions. This technique is useful for ensuring that the output is relevant and of high quality.\nTo use the instruction prompting technique, you need to provide the model with a clear and concise task, along with specific instructions to follow.\nFor example, if you are generating a customer service response, you would provide a task such as "generate a response to a customer query", along with an instruction such as "the response should be professional and provide accurate information".\nPrompt formula: "Following these instructions generate [task]: [instruction]"\nExamples:\nGenerate a customer service response:\nTask: generate a response to a customer query\nInstruction: the response should be professional and provide accurate information\nPrompt formula: "Following these instructions, generate a professional and accurate customer query response: the response should be professional and provide accurate information."\nGenerate a legal document:\nTask: generate a legal document\nInstruction: the document should comply with relevant laws and regulations\nPrompt formula: "Following these instructions, generate a legal document that complies with relevant laws and regulations: the document should comply with relevant laws and regulations."\nWhen using the instruction prompting technique, it is important to remember that the instructions should be clear and specific. This will help ensure that the output is relevant and of high quality. The instruction prompting technique can be combined with the "role prompting" and "seed-word prompting" techniques explained in the next chapter to enhance ChatGPT\'s output.\n\n'])
    ```

- File-based chat
    ```python3
    # knowledge_id is the return value of /knowledge_base/upload_temp_docs
    base_url = "http://127.0.0.1:7861/knowledge_base/temp_kb/{knowledge_id}"
    data = {
        "model": "qwen2-instruct",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello, I am an AI large language model"},
            {"role": "user", "content": "How do I ask high-quality questions?"},
        ],
        "stream": True,
        "temperature": 0.7,
        "extra_body": {
          "top_k": 3,
          "score_threshold": 2.0,
          "return_direct": True,
        },
    }

    import openai
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    resp = client.chat.completions.create(**data)
    for r in resp:
        print(r)
    ```

- Search engine Q&A
    ```python3
    engine_name = "bing" # available values: bing, duckduckgo, metaphor, searx
    base_url = f"http://127.0.0.1:7861/knowledge_base/search_engine/{engine_name}"
    data = {
        "model": "qwen2-instruct",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello, I am an AI large language model"},
            {"role": "user", "content": "How do I ask high-quality questions?"},
        ],
        "stream": True,
        "temperature": 0.7,
        "extra_body": {
          "top_k": 3,
          "score_threshold": 2.0,
          "return_direct": True,
        },
    }

    import openai
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    resp = client.chat.completions.create(**data)
    for r in resp:
        print(r)
    ```
