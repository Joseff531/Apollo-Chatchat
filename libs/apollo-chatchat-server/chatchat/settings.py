from __future__ import annotations

import os
from pathlib import Path
import sys
import typing as t

import nltk

from chatchat import __version__
from chatchat.pydantic_settings_file import *


# chatchat data directory; must be set via an environment variable. If not set, the current directory is used.
CHATCHAT_ROOT = Path(os.environ.get("CHATCHAT_ROOT", ".")).resolve()

XF_MODELS_TYPES = {
    "text2image": {"model_family": ["stable_diffusion"]},
    "image2image": {"model_family": ["stable_diffusion"]},
    "speech2text": {"model_family": ["whisper"]},
    "text2speech": {"model_family": ["ChatTTS"]},
}


class BasicSettings(BaseFileSettings):
    """
    Basic server configuration.
    Changes to log_verbose / HTTPX_DEFAULT_TIMEOUT take effect immediately.
    All other settings require restarting the server to take effect; do not modify them while the service is running.
    """

    model_config = SettingsConfigDict(yaml_file=CHATCHAT_ROOT / "basic_settings.yaml")

    version: str = __version__
    """Project code version used to generate this configuration template. If this value does not match the running program version, it is recommended to regenerate the configuration template."""

    log_verbose: bool = False
    """Whether to enable verbose logging."""

    HTTPX_DEFAULT_TIMEOUT: float = 300
    """Default timeout (in seconds) for httpx requests. If model loading or chats are slow and you encounter timeout errors, increase this value."""

    # @computed_field
    @cached_property
    def PACKAGE_ROOT(self) -> Path:
        """Code root directory"""
        return Path(__file__).parent

    # @computed_field
    @cached_property
    def DATA_PATH(self) -> Path:
        """User data root directory"""
        p = CHATCHAT_ROOT / "data"
        return p

    # @computed_field
    @cached_property
    def IMG_DIR(self) -> Path:
        """Project image directory"""
        p = self.PACKAGE_ROOT / "img"
        return p

    # @computed_field
    @cached_property
    def NLTK_DATA_PATH(self) -> Path:
        """nltk model storage path"""
        p = self.PACKAGE_ROOT / "data/nltk_data"
        return p

    # @computed_field
    @cached_property
    def LOG_PATH(self) -> Path:
        """Log storage path"""
        p = self.DATA_PATH / "logs"
        return p

    # @computed_field
    @cached_property
    def MEDIA_PATH(self) -> Path:
        """Storage location for model-generated content (images, videos, audio, etc.)"""
        p = self.DATA_PATH / "media"
        return p

    # @computed_field
    @cached_property
    def BASE_TEMP_DIR(self) -> Path:
        """Temporary file directory, primarily used for file chats"""
        p = self.DATA_PATH / "temp"
        (p / "openai_files").mkdir(parents=True, exist_ok=True)
        return p

    KB_ROOT_PATH: str = str(CHATCHAT_ROOT / "data/knowledge_base")
    """Default storage path for knowledge bases"""

    DB_ROOT_PATH: str = str(CHATCHAT_ROOT / "data/knowledge_base/info.db")
    """Default database storage path. When using sqlite, you can modify DB_ROOT_PATH directly; for other databases, modify SQLALCHEMY_DATABASE_URI instead."""

    SQLALCHEMY_DATABASE_URI:str = "sqlite:///" + str(CHATCHAT_ROOT / "data/knowledge_base/info.db")
    """Connection URI for the knowledge base info database"""

    OPEN_CROSS_DOMAIN: bool = False
    """Whether to enable cross-origin requests for the API"""

    DEFAULT_BIND_HOST: str = "0.0.0.0" if sys.platform != "win32" else "127.0.0.1"
    """
    Default host that each server binds to. If you change it to "0.0.0.0", you must also update the host of every XX_SERVER below.
    On Windows, when the WEBUI automatically launches the browser, "0.0.0.0" is unreachable; you must manually edit the address bar.
    """

    API_SERVER: dict = {"host": DEFAULT_BIND_HOST, "port": 7861, "public_host": "127.0.0.1", "public_port": 7861}
    """API server address. public_host is used to generate public access URLs for cloud services (e.g., knowledge base document links)."""

    WEBUI_SERVER: dict = {"host": DEFAULT_BIND_HOST, "port": 8501}
    """WEBUI server address"""

    def make_dirs(self):
        '''Create all data directories'''
        for p in [
            self.DATA_PATH,
            self.MEDIA_PATH,
            self.LOG_PATH,
            self.BASE_TEMP_DIR,
        ]:
            p.mkdir(parents=True, exist_ok=True)
        for n in ["image", "audio", "video"]:
            (self.MEDIA_PATH / n).mkdir(parents=True, exist_ok=True)
        Path(self.KB_ROOT_PATH).mkdir(parents=True, exist_ok=True)


class KBSettings(BaseFileSettings):
    """Knowledge base related configuration"""

    model_config = SettingsConfigDict(yaml_file=CHATCHAT_ROOT / "kb_settings.yaml")

    DEFAULT_KNOWLEDGE_BASE: str = "samples"
    """Default knowledge base to use"""

    DEFAULT_VS_TYPE: t.Literal["faiss", "milvus", "zilliz", "pg", "es", "relyt", "chromadb"] = "faiss"
    """Default vector store / full-text search engine type"""

    CACHED_VS_NUM: int = 1
    """Number of cached vector stores (for FAISS)"""

    CACHED_MEMO_VS_NUM: int = 10
    """Number of cached temporary vector stores (for FAISS), used for file chats"""

    CHUNK_SIZE: int = 750
    """Length of a single text chunk in the knowledge base (not applicable to MarkdownHeaderTextSplitter)"""

    OVERLAP_SIZE: int = 150
    """Overlap length between adjacent text chunks in the knowledge base (not applicable to MarkdownHeaderTextSplitter)"""

    VECTOR_SEARCH_TOP_K: int = 3 # TODO: duplicate with tool configuration
    """Number of vectors to retrieve from the knowledge base"""

    SCORE_THRESHOLD: float = 2.0
    """Knowledge base relevance score threshold, between 0 and 2. A smaller SCORE means higher relevance; 2 is equivalent to no filtering. Around 0.5 is recommended."""

    DEFAULT_SEARCH_ENGINE: t.Literal["bing", "duckduckgo", "metaphor", "searx"] = "duckduckgo"
    """Default search engine"""

    SEARCH_ENGINE_TOP_K: int = 3
    """Number of results to fetch from the search engine"""

    ZH_TITLE_ENHANCE: bool = False
    """Whether to enable Chinese title enhancement, along with related title enhancement settings"""

    PDF_OCR_THRESHOLD: t.Tuple[float, float] = (0.6, 0.6)
    """
    PDF OCR control: only run OCR on images whose width and height exceed a certain ratio of the page (image width / page width, image height / page height).
    This avoids interference from small images inside the PDF and speeds up processing of non-scanned PDFs.
    """

    KB_INFO: t.Dict[str, str] = {"samples": "Answers to issues about this project"} # TODO: now that everything is stored in the database, is this configuration still necessary?
    """Initialization description for each knowledge base, used during knowledge base initialization and Agent invocation. If empty, no description is provided and the knowledge base will not be invoked by the Agent."""

    kbs_config: t.Dict[str, t.Dict] = {
            "faiss": {},
            "milvus": {
                "host": "127.0.0.1",
                "port": "19530",
                "user": "",
                "password": "",
                "secure": False
            },
            "zilliz": {
                "host": "in01-a7ce524e41e3935.ali-cn-hangzhou.vectordb.zilliz.com.cn",
                "port": "19530",
                "user": "",
                "password": "",
                "secure": True
            },
            "pg": {
                "connection_uri": "postgresql://postgres:postgres@127.0.0.1:5432/langchain_chatchat"
            },
            "relyt": {
                "connection_uri": "postgresql+psycopg2://postgres:postgres@127.0.0.1:7000/langchain_chatchat"
            },
            "es": {
                "scheme": "http",
                "host": "127.0.0.1",
                "port": "9200",
                "index_name": "test_index",
                "user": "",
                "password": "",
                "verify_certs": True,
                "ca_certs": None,
                "client_cert": None,
                "client_key": None
            },
            "milvus_kwargs": {
                "search_params": {
                    "metric_type": "L2"
                },
                "index_params": {
                    "metric_type": "L2",
                    "index_type": "HNSW"
                }
            },
            "chromadb": {}
        }
    """Available vector store types and their corresponding configuration"""

    text_splitter_dict: t.Dict[str, t.Dict[str, t.Any]] = {
            "ChineseRecursiveTextSplitter": {
                "source": "",
                "tokenizer_name_or_path": "",
            },
            "SpacyTextSplitter": {
                "source": "huggingface",
                "tokenizer_name_or_path": "gpt2",
            },
            "RecursiveCharacterTextSplitter": {
                "source": "tiktoken",
                "tokenizer_name_or_path": "cl100k_base",
            },
            "MarkdownHeaderTextSplitter": {
                "headers_to_split_on": [
                    ("#", "head1"),
                    ("##", "head2"),
                    ("###", "head3"),
                    ("####", "head4"),
                ]
            },
        }
    """
    TextSplitter configuration. If you do not understand the meaning, do not modify it.
    If source is set to tiktoken, OpenAI's method is used; otherwise "huggingface".
    """

    TEXT_SPLITTER_NAME: str = "ChineseRecursiveTextSplitter"
    """TEXT_SPLITTER name"""

    EMBEDDING_KEYWORD_FILE: str = "embedding_keywords.txt"
    """Vocabulary file of custom keywords for the Embedding model"""


class PlatformConfig(MyBaseModel):
    """Model platform configuration"""

    platform_name: str = "xinference"
    """Platform name"""

    platform_type: t.Literal["xinference", "ollama", "oneapi", "fastchat", "openai", "custom openai"] = "xinference"
    """Platform type"""

    api_base_url: str = "http://127.0.0.1:9997/v1"
    """openai api url"""

    api_key: str = "EMPTY"
    """api key if available"""

    api_proxy: str = ""
    """API proxy"""

    api_concurrencies: int = 5
    """Maximum concurrency per model on this platform"""

    auto_detect_model: bool = False
    """Whether to automatically detect the available model list on the platform. When set to True, the different model types below can be auto-detected."""

    llm_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of large language models supported by this platform. Auto-detected when auto_detect_model is True."""

    embed_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of embedding models supported by this platform. Auto-detected when auto_detect_model is True."""

    text2image_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of image generation models supported by this platform. Auto-detected when auto_detect_model is True."""

    image2text_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of multimodal models supported by this platform. Auto-detected when auto_detect_model is True."""

    rerank_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of rerank models supported by this platform. Auto-detected when auto_detect_model is True."""

    speech2text_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of STT models supported by this platform. Auto-detected when auto_detect_model is True."""

    text2speech_models: t.Union[t.Literal["auto"], t.List[str]] = []
    """List of TTS models supported by this platform. Auto-detected when auto_detect_model is True."""


class ApiModelSettings(BaseFileSettings):
    """Model configuration"""

    model_config = SettingsConfigDict(yaml_file=CHATCHAT_ROOT / "model_settings.yaml")

    DEFAULT_LLM_MODEL: str = "glm4-chat"
    """Default LLM model name"""

    DEFAULT_EMBEDDING_MODEL: str = "bge-m3"
    """Default Embedding model name"""

    Agent_MODEL: str = "" # TODO: appears to duplicate LLM_MODEL_CONFIG
    """Name of the AgentLM model (optional; if specified, the model used by the Chain entered by the Agent is locked; if not specified, DEFAULT_LLM_MODEL is used)."""

    HISTORY_LEN: int = 3
    """Default number of history rounds"""

    MAX_TOKENS: t.Optional[int] = None # TODO: appears to duplicate LLM_MODEL_CONFIG
    """Maximum length supported by the large model. If left empty, the model's default maximum length is used; otherwise, the user-specified maximum length is used."""

    TEMPERATURE: float = 0.7
    """General LLM chat parameter"""

    SUPPORT_AGENT_MODELS: t.List[str] = [
            "chatglm3-6b",
            "glm-4",
            "openai-api",
            "Qwen-2",
            "qwen2-instruct",
            "gpt-3.5-turbo",
            "gpt-4o",
        ]
    """Supported Agent models"""

    LLM_MODEL_CONFIG: t.Dict[str, t.Dict] = {
            # Intent recognition does not need to produce output; the model only needs to know in the background
            "preprocess_model": {
                "model": "",
                "temperature": 0.05,
                "max_tokens": 4096,
                "history_len": 10,
                "prompt_name": "default",
                "callbacks": False,
            },
            "llm_model": {
                "model": "",
                "temperature": 0.9,
                "max_tokens": 4096,
                "history_len": 10,
                "prompt_name": "default",
                "callbacks": True,
            },
            "action_model": {
                "model": "",
                "temperature": 0.01,
                "max_tokens": 4096,
                "history_len": 10,
                "prompt_name": "ChatGLM3",
                "callbacks": True,
            },
            "postprocess_model": {
                "model": "",
                "temperature": 0.01,
                "max_tokens": 4096,
                "history_len": 10,
                "prompt_name": "default",
                "callbacks": True,
            },
            "image_model": {
                "model": "sd-turbo",
                "size": "256*256",
            },
        }
    """
    LLM model configuration, including initialization parameters for different modalities.
    If `model` is left empty, DEFAULT_LLM_MODEL is used automatically.
    """

    MODEL_PLATFORMS: t.List[PlatformConfig] = [
            PlatformConfig(**{
                "platform_name": "xinference",
                "platform_type": "xinference",
                "api_base_url": "http://127.0.0.1:9997/v1",
                "api_key": "EMPTY",
                "api_concurrencies": 5,
                "auto_detect_model": True,
                "llm_models": [],
                "embed_models": [],
                "text2image_models": [],
                "image2text_models": [],
                "rerank_models": [],
                "speech2text_models": [],
                "text2speech_models": [],
            }),
            PlatformConfig(**{
                "platform_name": "ollama",
                "platform_type": "ollama",
                "api_base_url": "http://127.0.0.1:11434/v1",
                "api_key": "EMPTY",
                "api_concurrencies": 5,
                "llm_models": [
                    "qwen:7b",
                    "qwen2:7b",
                ],
                "embed_models": [
                    "quentinz/bge-large-zh-v1.5",
                ],
            }),
            PlatformConfig(**{
                "platform_name": "oneapi",
                "platform_type": "oneapi",
                "api_base_url": "http://127.0.0.1:3000/v1",
                "api_key": "sk-",
                "api_concurrencies": 5,
                "llm_models": [
                    # Zhipu API
                    "chatglm_pro",
                    "chatglm_turbo",
                    "chatglm_std",
                    "chatglm_lite",
                    # Qwen API
                    "qwen-turbo",
                    "qwen-plus",
                    "qwen-max",
                    "qwen-max-longcontext",
                    # Qianfan API
                    "ERNIE-Bot",
                    "ERNIE-Bot-turbo",
                    "ERNIE-Bot-4",
                    # Spark API
                    "SparkDesk",
                ],
                "embed_models": [
                    # Qwen API
                    "text-embedding-v1",
                    # Qianfan API
                    "Embedding-V1",
                ],
                "text2image_models": [],
                "image2text_models": [],
                "rerank_models": [],
                "speech2text_models": [],
                "text2speech_models": [],
            }),
            PlatformConfig(**{
                "platform_name": "openai",
                "platform_type": "openai",
                "api_base_url": "https://api.openai.com/v1",
                "api_key": "sk-proj-",
                "api_concurrencies": 5,
                "llm_models": [
                    "gpt-4o",
                    "gpt-3.5-turbo",
                ],
                "embed_models": [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                ],
            }),
        ]
    """Model platform configuration"""


class ToolSettings(BaseFileSettings):
    """Agent tool configuration"""
    model_config = SettingsConfigDict(yaml_file=CHATCHAT_ROOT / "tool_settings.yaml",
                                      json_file=CHATCHAT_ROOT / "tool_settings.json",
                                      extra="allow")

    search_local_knowledgebase: dict = {
        "use": False,
        "top_k": 3,
        "score_threshold": 2.0,
        "conclude_prompt": {
            "with_result": '<instruction>Answer the question concisely and professionally based on the known information. If the answer cannot be derived from it, say "The question cannot be answered based on the known information",'
            "do not allow fabricated content in the answer, and please answer in English. </instruction>\n"
            "<known_information>{{ context }}</known_information>\n"
            "<question>{{ question }}</question>\n",
            "without_result": "Please answer my question based on my prompt:\n"
            "{{ question }}\n"
            "Note that at the end of your answer you must emphasize that your answer is based on your experience and not on reference materials.\n",
        },
    }
    '''Local knowledge base tool configuration'''

    search_internet: dict = {
        "use": False,
        "search_engine_name": "duckduckgo",
        "search_engine_config": {
            "bing": {
                "bing_search_url": "https://api.bing.microsoft.com/v7.0/search",
                "bing_key": "",
            },
            "metaphor": {
                "metaphor_api_key": "",
                "split_result": False,
                "chunk_size": 500,
                "chunk_overlap": 0,
            },
            "duckduckgo": {},
            "searx": {
                "host": "https://metasearx.com",
                "engines": [],
                "categories": [],
                "language": "zh-CN",
            }
        },
        "top_k": 5,
        "verbose": "Origin",
        "conclude_prompt": "<instruction>This is information searched from the internet. Please extract from it and answer the question concisely and coherently. If the answer cannot be derived, say \"Unable to find content that answers the question\". "
        "</instruction>\n<known_information>{{ context }}</known_information>\n"
        "<question>\n"
        "{{ question }}\n"
        "</question>\n",
    }
    '''Search engine tool configuration. It is recommended to deploy your own searx search engine for the most convenient use.'''

    arxiv: dict = {
        "use": False,
    }

    weather_check: dict = {
        "use": False,
        "api_key": "",
    }
    '''Seniverse Weather (https://www.seniverse.com/) tool configuration'''

    search_youtube: dict = {
        "use": False,
    }

    wolfram: dict = {
        "use": False,
        "appid": "",
    }

    calculate: dict = {
        "use": False,
    }
    '''numexpr math calculation tool configuration'''

    text2images: dict = {
        "use": False,
        "model": "sd-turbo",
        "size": "256*256",
    }
    '''Image generation tool configuration. The model must be configured in model_settings.yaml/MODEL_PLATFORMS.'''

    text2sql: dict = {
        # This tool requires a separately specified large model, independent of the model selected by the user on the front end
        "model_name": "qwen-plus",
        "use": False,
        # SQLAlchemy connection string. Supported databases are:
        # crate, duckdb, googlesql, mssql, mysql, mariadb, oracle, postgresql, sqlite, clickhouse, prestodb
        # For other databases, please consult SQLAlchemy usage, modify sqlalchemy_connect_str, and configure the corresponding database connection. For example, sqlite uses sqlite:///path-to-database-file. The example below is for mysql.
        # If the driver for the corresponding database is missing, please install it yourself via poetry.
        "sqlalchemy_connect_str": "mysql+pymysql://username:password@host/database_name",
        # Be sure to evaluate whether to enable read_only. When enabled, SQL statements will be checked. Please confirm whether the intercept_sql interceptor in text2sql.py satisfies the read-only requirements of the database you are using.
        # It is preferable to restrict user permissions at the database level.
        "read_only": False,
        # Limit on the number of returned rows
        "top_k": 50,
        # Whether to return intermediate steps
        "return_intermediate_steps": True,
        # To specify particular tables, fill in the table names such as ["sys_user", "sys_dept"]. If left empty, the tool will rely on intelligent judgment to decide which tables to use.
        "table_names": [],
        # Provide additional descriptions of table names to help the large model better decide which tables to use. This is especially important in SQLDatabaseSequentialChain mode, where predictions are based on table names and misjudgments are easy.
        "table_comments": {
            # If the large model picks the wrong table, you can try filling in table names and descriptions according to the actual situation
            # "tableA": "This is a user table that stores basic user information",
            # "tableB": "Role table",
        },
    }
    '''
    text2sql usage recommendations
    1. Because SQL generated by large models may deviate from expectations, please be sure to test and evaluate thoroughly in a test environment;
    2. In production, for query operations, because query efficiency is uncertain, it is recommended to adopt a primary-replica database architecture and let text2sql connect to the replica database to prevent possible slow queries from affecting the primary business;
    3. Be cautious with write operations. If write operations are not needed, set read_only to True and, preferably, revoke write permissions of the database user at the database level to prevent users from modifying the database via natural language;
    4. text2sql depends on the large model's capabilities in intent understanding and SQL conversion. Different large models can be tested for comparison;
    5. Database table names and field names should match their actual function and be easy to understand. Detailed comments should be added to database tables and fields to help the large model better understand the database structure;
    6. If the existing database table names are hard for the large model to understand, you can configure the table_comments field below to supplement the descriptions of certain tables.
    '''

    amap: dict = {
        "use": False,
        "api_key": "Amap API KEY",
    }
    '''Amap map and weather tool configuration.'''

    text2promql: dict = {
        "use": False,
        # <your_prometheus_ip>:<your_prometheus_port>
        "prometheus_endpoint": "http://127.0.0.1:9090",
        # <your_prometheus_username>
        "username": "",
        # <your_prometheus_password>
        "password": "",
    }
    '''
    text2promql usage recommendations
    1. Because the PromQL generated by large models may deviate from expectations, please be sure to test and evaluate thoroughly in a test environment;
    2. text2promql depends on the large model's capabilities in intent understanding, metric selection, and PromQL conversion; different large models can be tested for comparison;
    3. Currently only single-Prometheus queries are supported; multi-Prometheus queries may be supported in the future.
    '''

    url_reader: dict = {
        "use": False,
        "timeout": "10000",
    }
    '''URL content reader (https://r.jina.ai/) tool configuration.
    Please make sure the deployment network environment is good to avoid issues like timeouts.'''



class PromptSettings(BaseFileSettings):
    """Prompt templates. All templates use jinja2 format except the Agent template, which uses f-string."""

    model_config = SettingsConfigDict(yaml_file=CHATCHAT_ROOT / "prompt_settings.yaml",
                                      json_file=CHATCHAT_ROOT / "prompt_settings.json",
                                      extra="allow")

    preprocess_model: dict = {
        "default": (
            "Reply with only 0 or 1, indicating whether a tool is not needed. The following kinds of questions do not require a tool:\n"
            "1. Content that requires online lookup\n"
            "2. Content that requires calculation\n"
            "3. Content that requires real-time data\n"
            "If my input matches any of these cases, return 1. For other inputs, reply with 0. Just return a single number.\n"
            "Here is my question:"
            ),
    }
    """Template for intent recognition"""

    llm_model: dict = {
        "default": "{{input}}",
        "with_history": (
            "The following is a friendly conversation between a human and an AI.\n"
            "The AI is talkative and provides lots of specific details from its context.\n"
            "If the AI does not know the answer to a question, it truthfully says it does not know.\n\n"
            "Current conversation:\n"
            "{{history}}\n"
            "Human: {{input}}\n"
            "AI:"
            ),
    }
    '''Template for regular LLM chat'''

    rag: dict = {
        "default": (
            "[Instruction] Answer the question concisely and professionally based on the known information. "
            "If the answer cannot be derived from it, say \"The question cannot be answered based on the known information\". Do not allow fabricated content in the answer. Please answer in English.\n\n"
            "[Known Information] {{context}}\n\n"
            "[Question] {{question}}\n"
            ),
        "empty": (
            "Please answer my question:\n"
            "{{question}}"
        ),
    }
    '''RAG template, can be used for knowledge base Q&A, file chat, and search engine chat'''

    action_model: dict = {
        "default": {
            "SYSTEM_PROMPT": (
                "You are a helpful assistant"
            ),
        },
        "openai-functions": {
            "SYSTEM_PROMPT": (
                "You are a helpful assistant"
            ),
            "HUMAN_MESSAGE": (
                "{input}"
            )
        },
        "glm3": {
            "SYSTEM_PROMPT": ("\nAnswer the following questions as best as you can. You have access to the following "
                              "tools:\n{tools}"),
            "HUMAN_MESSAGE": "Let's start! Human:{input}\n\n{agent_scratchpad}"

        },
        "qwen": {
            "SYSTEM_PROMPT": (
                "Answer the following questions as best you can. You have access to the following APIs:\n\n"
                "{tools}\n\n"
                "Use the following format:\n\n"
                "Question: the input question you must answer\n"
                "Thought: you should always think about what to do\n"
                "Action: the action to take, should be one of [{tool_names}]\n"
                "Action Input: the input to the action\n"
                "Observation: the result of the action\n"
                "... (this Thought/Action/Action Input/Observation can be repeated zero or more times)\n"
                "Thought: I now know the final answer\n"
                "Final Answer: the final answer to the original input question\n\n"
                "Format the Action Input as a JSON object.\n\n"
                "Begin!\n\n"),
            "HUMAN_MESSAGE": (
                "Question: {input}\n\n"
                "{agent_scratchpad}\n\n")
        },
        "structured-chat-agent": {
            "SYSTEM_PROMPT": (
                "Respond to the human as helpfully and accurately as possible. You have access to the following tools:\n\n"
                "{tools}\n\n"
                "Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).\n\n"
                'Valid "action" values: "Final Answer" or {tool_names}\n\n'
                "Provide only ONE action per $JSON_BLOB, as shown:\n\n"
                '```\n{{\n  "action": $TOOL_NAME,\n  "action_input": $INPUT\n}}\n```\n\n'
                "Follow this format:\n\n"
                "Question: input question to answer\n"
                "Thought: consider previous and subsequent steps\n"
                "Action:\n```\n$JSON_BLOB\n```\n"
                "Observation: action result\n"
                "... (repeat Thought/Action/Observation N times)\n"
                "Thought: I know what to respond\n"
                'Action:\n```\n{{\n  "action": "Final Answer",\n  "action_input": "Final response to human"\n}}\n\n'
                "Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary. Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation\n"
            ),
            "HUMAN_MESSAGE": (
                "{input}\n\n"
                "{agent_scratchpad}\n\n"
            )
            # '(reminder to respond in a JSON blob no matter what)')
        },
        "platform-agent": {
            "SYSTEM_PROMPT": (
                "You are a helpful assistant"
            ),
            "HUMAN_MESSAGE": (
                "{input}\n\n"
            )
        },
        "platform-knowledge-mode": {
            "SYSTEM_PROMPT": (
                "</think>You are ChatChat,  a content manager, you are familiar with how to find data from complex projects and better respond to users\n"
                "\n"
                "\n"
                "CRITICAL: TOOL RULES: All tool usage MUST ` Tool Use Formatting` the specified structured format. \n"
                "CRITICAL: THINKING RULES: In <thinking> tags, assess what information you already have and what information you need to proceed with the task. Include detailed output description text within <thinking> tags and always specify the `TOOL USE` next action to take.\n"
                "CRITICAL: MCP TOOL RULES: All MCP tool usage MUST strictly follow the Output Structure rules defined for `use_mcp_tool`. The output will always be returned within <use_mcp_tool> tags with the specified structured format.\n"
                "IMPORTANT: This tool usage process will be repeated multiple times throughout task completion. Each and every MCP tool call MUST follow the Output Structure rules without exception. The structured format must be applied consistently across all iterations to ensure proper parsing and execution.\n"
                "\n"
                "====\n"
                "\n"
                "TOOL USE\n"
                "You have access to a set of tools that are executed upon the user's approval. You can use one tool per message, and will receive the result of that tool use in the user's response. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.\n"
                "\n"
                "CRITICAL: MCP TOOL RULES: All MCP tool usage MUST strictly follow the Output Structure rules defined for `use_mcp_tool`. The output will always be returned within <use_mcp_tool> tags with the specified structured format.\n"
                "IMPORTANT: This tool usage process will be repeated multiple times throughout task completion. Each and every MCP tool call MUST follow the Output Structure rules without exception. The structured format must be applied consistently across all iterations to ensure proper parsing and execution.\n"
                "\n"
                "# Tool Use Formatting\n"
                "\n"
                "CRITICAL: TOOL USE FORMATTING: Tool use is formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. This format is MANDATORY for proper parsing and execution. Here's the structure:\n"
                "\n"
                "<tool_name>\n"
                "<parameter1_name>value1</parameter1_name>\n"
                "<parameter2_name>value2</parameter2_name>\n"
                "...\n"
                "</tool_name>\n"
                "\n"
                "For example:\n"
                "\n"
                "<read_file>\n"
                "<path>src/main.js</path>\n"
                "</read_file>\n"
                "\n"
                "\n"
                "# Tools\n"
                "\n" 
                "{tools}\n"
                "\n" 
                "## use_mcp_tool\n"
                "Description: Request to use a tool provided by a connected MCP server. Each MCP server can provide multiple tools with different capabilities. Tools have defined input schemas that specify required and optional parameters.\n"
                "Parameters:\n"
                "- server_name: (required) The name of the MCP server providing the tool\n"
                "- tool_name: (required) The name of the tool to execute\n"
                "- arguments: (required) A JSON object containing the tool's input parameters, following the tool's input schema\n"
                "\n"
                "Usage:\n"
                "<use_mcp_tool>\n"
                "<server_name>server name here</server_name>\n"
                "<tool_name>tool name here</tool_name>\n"
                "<arguments>\n"
                "{{\n"
                "  \"param1\": \"value1\",\n"
                "  \"param2\": \"value2\"\n"
                "}}\n"
                "</arguments>\n"
                "</use_mcp_tool>\n"
                "\n"
                "Output Structure:\n"
                "The tool will return a structured response within <use_mcp_tool> tags containing:\n"
                "<use_mcp_tool>\n"
                "- success: boolean indicating if the tool execution succeeded\n"
                "- result: the actual output data from the tool execution\n"
                "- error: error message if the execution failed (null if successful)\n"
                "- server_name: the name of the MCP server that executed the tool\n"
                "- tool_name: the name of the tool that was executed\n"
                "</use_mcp_tool>\n"
                "\n"
                "\n"
                "## access_mcp_resource\n"
                "Description: Request to access a resource provided by a connected MCP server. Resources represent data sources that can be used as context, such as files, API responses, or system information.\n"
                "Parameters:\n"
                "- server_name: (required) The name of the MCP server providing the resource\n"
                "- uri: (required) The URI identifying the specific resource to access\n"
                "Usage:\n"
                "<access_mcp_resource>\n"
                "<server_name>server name here</server_name>\n"
                "<uri>resource URI here</uri>\n"
                "</access_mcp_resource>\n"
                "\n"
                "\n"
                "====\n"
                "\n"
                "# Tool Use Examples\n"
                "\n"
                "## Example 1: Requesting to use an MCP tool\n"
                "\n"
                "<use_mcp_tool>\n"
                "<server_name>weather-server</server_name>\n"
                "<tool_name>get_forecast</tool_name>\n"
                "<arguments>\n"
                "{{\n"
                "  \"city\": \"San Francisco\",\n"
                "  \"days\": 5\n"
                "}}\n"
                "</arguments>\n"
                "</use_mcp_tool>\n"
                "\n"
                "## Example 2: Requesting to access an MCP resource\n"
                "\n"
                "<access_mcp_resource>\n"
                "<server_name>weather-server</server_name>\n"
                "<uri>weather://san-francisco/current</uri>\n"
                "</access_mcp_resource>\n"
                "\n"
                "\n"
                "====\n"
                "\n"
                "MCP SERVERS\n"
                "\n"
                "The Model Context Protocol (MCP) enables communication between the system and locally running MCP servers that provide additional tools and resources to extend your capabilities.\n"
                "\n"
                "CRITICAL: MCP TOOL RULES: All MCP tool usage MUST strictly follow the Output Structure rules defined for `use_mcp_tool`. The output will always be returned within <use_mcp_tool> tags with the specified structured format.\n"
                "IMPORTANT: This tool usage process will be repeated multiple times throughout task completion. Each and every MCP tool call MUST follow the Output Structure rules without exception. The structured format must be applied consistently across all iterations to ensure proper parsing and execution.\n"
                "\n"
                "# Connected MCP Servers\n"
                "\n"
                "When a server is connected, you can use the server's tools via the `use_mcp_tool` tool, and access the server's resources via the `access_mcp_resource` tool.\n"
                "\n"
                "\n"
                "{mcp_tools}\n"
                "\n"
                "\n"
                "====\n"
                "\n"
                "\n"
                "# Choosing the Appropriate Tool\n"
                "\n"
                "None\n"
                "\n"
                "\n"
                "====\n"
                "# Auto-formatting Considerations\n"
                " \n"
                "None\n"
                "\n"
                "\n"
                "====\n"
                "# Workflow Tips\n"
                "\n"
                "None\n"
                "\n"
                "\n"
                "====\n"
                " \n"
                "CAPABILITIES\n"
                "\n"
                "- You have access to tools that\n" 
                "\n"
                "- You have access to MCP servers that may provide additional tools and resources. Each server may provide different capabilities that you can use to accomplish tasks more effectively.\n"
                "\n"
                "\n"
                "====\n"
                "\n"
                "RULES\n"
                "\n"
                "CRITICAL: Always adhere to this format for the tool use to ensure proper parsing and execution. Before completing the user's final task, all intermediate tool usage processes must maintain proper parsing and execution. Each tool call must be correctly formatted and executed according to the specified XML structure to ensure successful task completion.\n"
                "CRITICAL: MCP TOOL RULES: 1. All MCP tool output must be enclosed within <use_mcp_tool> opening and closing tags without exception.\n"
                "CRITICAL: MCP TOOL RULES: 2. The structured response format must be strictly followed for proper parsing and execution.\n"
                "CRITICAL: MCP TOOL RULES: 3. Before completing user's final task, all intermediate MCP tool processes must maintain proper parsing and execution.\n"
                "CRITICAL: THINKING RULES: In <thinking> tags, assess what information you already have and what information you need to proceed with the task. Include detailed output description text within <thinking> tags and always specify the `TOOL USE` next action to take.\n"
                "CRITICAL: PARAMETER RULES: 1. ALL parameters marked as (required) MUST be provided with actual content - empty or null values are strictly forbidden.\n"
                "CRITICAL: PARAMETER RULES: 2. The 'uri' parameter MUST contain a valid resource URI string.\n"
                "CRITICAL: PARAMETER RULES: 3. Missing parameters or empty parameter values will cause resource access to fail.\n" 
                "CRITICAL: PARAMETER RULES: 4. ALL parameters marked as (required) MUST be provided with actual content - empty or null values are strictly forbidden.\n"
                "CRITICAL: PARAMETER RULES: 5. The 'arguments' parameter MUST contain a valid JSON object with appropriate parameter values for the specified tool.\n"
                "CRITICAL: PARAMETER RULES: 6. Missing parameters or empty parameter values will cause tool execution to fail.\n"
                "CRITICAL: Tool Use RULES: 1. If multiple actions are needed, use one tool at a time per message to accomplish the task iteratively, with each tool use being informed by the result of the previous tool use. Do not assume the outcome of any tool use. Each step must be informed by the previous step's result.\n"
                "CRITICAL: Tool Use RULES: 2. Formulate your tool use using the XML format specified for each tool. by example `TOOL USE`\n"
                "Your current working directory is: {current_working_directory}\n"
                "You are STRICTLY FORBIDDEN from starting your messages with \"Great\", \"Certainly\", \"Okay\", \"Sure\". You should NOT be conversational in your responses, but rather direct and to the point. For example you should NOT say \"Great, I've find's the Chunk\" but instead something like \"I've find's the Chunk\". It is important you be clear and technical in your messages.\n"
                "When presented with images, utilize your vision capabilities to thoroughly examine them and extract meaningful information. Incorporate these insights into your thought process as you accomplish the user's task.\n"
                "At the end of each user message, you will automatically receive environment_details. This information is not written by the user themselves, but is auto-generated to provide potentially relevant context about the project structure and environment. While this information can be valuable for understanding the project context, do not treat it as a direct part of the user's request or response. Use it to inform your actions and decisions, but don't assume the user is explicitly asking about or referring to this information unless they clearly do so in their message. When using environment_details, explain your actions clearly to ensure the user understands, as they may not be aware of these details.\n"
                "MCP operations should be used one at a time, similar to other tool usage. Wait for confirmation of success before proceeding with additional operations.\n"
               
                "\n"
                "\n"
                "====\n"
                "\n"
                "SYSTEM INFORMATION\n"
                "\n"
                "None\n"
                "\n"
                "====\n"
                "\n"
                "OBJECTIVE\n"
                "\n"
                "You accomplish a given task iteratively, breaking it down into clear steps and working through them methodically.\n"
                "\n"
                "1. Analyze the user's task and set clear, achievable goals to accomplish it. Prioritize these goals in a logical order.\n"
                "2. Work through these goals sequentially, utilizing available tools one at a time as necessary. Each goal should correspond to a distinct step in your problem-solving process. You will be informed on the work completed and what's remaining as you go.\n"
                "3. Remember, you have extensive capabilities with access to a wide range of tools that can be used in powerful and clever ways as necessary to accomplish each goal. Before calling a tool, do some analysis within <thinking></thinking> tags. First, analyze the file structure provided in environment_details to gain context and insights for proceeding effectively. Then, think about which of the provided tools is the most relevant tool to accomplish the user's task.\n"
                "4. The user may provide feedback, which you can use to make improvements and try again. But DO NOT continue in pointless back and forth conversations, i.e. don't end your responses with questions or offers for further assistance.\n"
            ),
            "HUMAN_MESSAGE": (
                "{input}\n\n" 
                "<environment_details>\n"
                "# Current Time\n"
                "{datetime}\n"
                "</environment_details>\n"
            )
        },
    }
    """Agent template"""

    postprocess_model: dict = {
        "default": "{{input}}",
    }
    """Post-processing template"""


class SettingsContainer:
    CHATCHAT_ROOT = CHATCHAT_ROOT

    basic_settings: BasicSettings = settings_property(BasicSettings())
    kb_settings: KBSettings = settings_property(KBSettings())
    model_settings: ApiModelSettings = settings_property(ApiModelSettings())
    tool_settings: ToolSettings = settings_property(ToolSettings())
    prompt_settings: PromptSettings = settings_property(PromptSettings())

    def createl_all_templates(self):
        self.basic_settings.create_template_file(write_file=True)
        self.kb_settings.create_template_file(write_file=True)
        self.model_settings.create_template_file(sub_comments={
            "MODEL_PLATFORMS": {"model_obj": PlatformConfig(),
                                "is_entire_comment": True}},
            write_file=True)
        self.tool_settings.create_template_file(write_file=True, file_format="yaml", model_obj=ToolSettings())
        self.prompt_settings.create_template_file(write_file=True, file_format="yaml")

    def set_auto_reload(self, flag: bool=True):
        self.basic_settings.auto_reload = flag
        self.kb_settings.auto_reload = flag
        self.model_settings.auto_reload = flag
        self.tool_settings.auto_reload = flag
        self.prompt_settings.auto_reload = flag


Settings = SettingsContainer()
nltk.data.path.append(str(Settings.basic_settings.NLTK_DATA_PATH))


if __name__ == "__main__":
    Settings.createl_all_templates()
