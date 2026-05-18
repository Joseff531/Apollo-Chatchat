### Project Overview
![](https://github.com/Joseff531/Apollo-Chatchat/blob/master/docs/img/logo-long-chatchat-trans-v2.png)

[![pypi badge](https://img.shields.io/pypi/v/apollo-chatchat.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/python-3.10%7C3.11-blue.svg)](https://pypi.org/project/pypiserver/)

# Apollo-Chatchat

An open-source, offline-deployable RAG and Agent application built on top of large language models such as ChatGLM and the LangChain application framework.

See the [project repo](https://github.com/Joseff531/Apollo-Chatchat) for full details.

### Installation

1. PyPI

```shell
pip install apollo-chatchat

# Or, if you use Xinference to serve models:
# pip install apollo-chatchat[xinference]

# When upgrading from an older version, re-run init to refresh the YAML templates:
# pip install -U apollo-chatchat
# chatchat init
```

See the [installation guide](https://github.com/Joseff531/Apollo-Chatchat#quick-start) for details.

> Install `apollo-chatchat` in a dedicated virtual environment (conda, venv, virtualenv, etc.).
>
> Known issue: do not install it side-by-side with Xinference in the same environment — some plugins (e.g. file upload) will break.

2. Source install

You can also [run from source](https://github.com/Joseff531/Apollo-Chatchat/blob/master/docs/contributing/README_dev.md). (Tip: running from source makes it easier to track down bugs or improve the project, but it is not recommended for first-time users.)

3. Docker

```shell
docker pull apolloimage/apollo-chatchat:0.3.1.3
```

> [!important]
> We strongly recommend using docker-compose; see [README_docker](https://github.com/Joseff531/Apollo-Chatchat/blob/master/docs/install/README_docker.md).

### Initialization and Configuration

The project needs a data directory and a set of configuration files. The following command generates the defaults (you can edit the YAML files at any time):

```shell
# Root path where data will be stored. Defaults to the current directory if unset.
export CHATCHAT_ROOT=/path/to/chatchat_data

# Initialize data directory and YAML configuration templates.
chatchat init
```

You will find `*_settings.yaml` files in `CHATCHAT_ROOT` (or in the current directory). Edit those files to pick the models you want; see the [initialization guide](https://github.com/Joseff531/Apollo-Chatchat#3-view-and-modify-the-apollo-chatchat-configuration) for details.

### Starting the Service

Once everything is configured (especially the LLM and embedding model), create the default knowledge base and start the service:

```shell
chatchat kb -r
chatchat start -a
```

If everything is fine, a browser window will pop up automatically.

Run `chatchat --help` for more commands.

### Changelog

#### 0.3.1.3 (2024-07-23)
- Fixed:
  - `nltk_data` was not being copied during project initialization.
  - Added `python-docx` as a dependency so docx files can be processed during knowledge-base initialization.

#### 0.3.1.2 (2024-07-20)
- New features:
    - Model platform now supports proxy configuration. (#4492)
    - Provided a default working searx server. (#4504)
    - Updated Docker images. (#4511)
    - Added a URL content reader: uses jina-ai/reader to turn URL content into LLM-friendly text. (#4547)
    - Improved JSON-repair success rate for tool calls under Qwen models. (#4554)
    - Allow users to configure `public_host` / `public_port` in `basic_settings.API_SERVER`, so the right public API URL is generated when running behind a cloud server or reverse proxy. (#4567)
    - Added automation scripts for models and services. (#4573)
    - Added unit tests. (#4573)
- Fixed:
    - Setting the system message in the WebUI had no effect. (#4491)
    - Removed the broken `vqa_processor` and `aqa_processor` tools. (#4498)
    - `KeyError: 'template'` error. (#4501)
    - `nltk_data` directory was set incorrectly during `chatchat init`. (#4523)
    - Xinference-client connection error during `chatchat init`. (#4573)
    - Xinference model auto-detection now uses a cache to speed up the UI. (#4510)
    - Duplicate entries in `chatchat.log`. (#4517)
    - Improved error-message propagation and frontend display. (#4531)
    - Fixed the argument shape passed to `openai.chat.completions.create` to improve compatibility. (#4540)
    - Milvus retriever `NotImplementedError`. (#4536)
    - Bug in using a ChromaDB collection as a retriever. (#4541)
    - After upgrading LangChain, `DocumentWithVsId` was getting duplicate IDs. (#4548)
    - Only one knowledge base was being processed during a full rebuild. (#4549)
    - Chat API error caused by OpenAPI defaulting `max_tokens` to 0. (#4564)

#### 0.3.1.1 (2024-07-15)
- Fixed:
  - Setting the system message in the WebUI had no effect. ([#4491](https://github.com/chatchat-space/Langchain-Chatchat/pull/4491))
  - Model platform did not support proxy configuration. ([#4492](https://github.com/chatchat-space/Langchain-Chatchat/pull/4492))
  - Removed the broken `vqa_processor` and `aqa_processor` tools. ([#4498](https://github.com/chatchat-space/Langchain-Chatchat/pull/4498))
  - Prompt-settings bug that caused `KeyError: 'template'`. ([#4501](https://github.com/chatchat-space/Langchain-Chatchat/pull/4501))
  - searx search engine did not support Chinese. ([#4504](https://github.com/chatchat-space/Langchain-Chatchat/pull/4504))
  - `chatchat init` tried to connect to Xinference by default and errored when no Xinference service was running. ([#4508](https://github.com/chatchat-space/Langchain-Chatchat/issues/4508))
  - During `init`, `shutil.copytree` errored when `src` and `dst` were the same path. ([#4507](https://github.com/chatchat-space/Langchain-Chatchat/pull/4507))

### Project Milestones

+ **April 2023**: Langchain-ChatGLM 0.1.0 released — local knowledge-base Q&A based on the ChatGLM-6B model.
+ **August 2023**: Langchain-ChatGLM renamed to Langchain-Chatchat; 0.2.0 released using `fastchat` as the model loading layer with support for more models and databases.
+ **October 2023**: Langchain-Chatchat 0.2.5 released with Agent functionality.
+ **December 2023**: Langchain-Chatchat passed 20K GitHub stars.
+ **June 2024**: Langchain-Chatchat 0.3.0 released with a new project architecture.
+ **Apollo-Chatchat fork**: Maintained by [Joseff531](https://github.com/Joseff531) — English-first, rebranded to Apollo-Chatchat.

---

### License

The code is licensed under [Apache-2.0](LICENSE).

### Citation

If this project helped your research, please cite the upstream project:

```
@software{langchain_chatchat,
    title        = {{langchain-chatchat}},
    author       = {Liu, Qian and Song, Jinke, and Huang, Zhiguo, and Zhang, Yuxuan, and glide-the, and Liu, Qingwei},
    year         = 2024,
    journal      = {GitHub repository},
    publisher    = {GitHub},
    howpublished = {\url{https://github.com/chatchat-space/Langchain-Chatchat}}
}
```
