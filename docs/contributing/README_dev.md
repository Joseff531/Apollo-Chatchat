# Apollo-Chatchat Source Code / Development Deployment Guide

## 0. Pull the Project Code

If you want to launch the project from source, please pull the master branch directly:

```shell
git clone https://github.com/Joseff531/Apollo-Chatchat.git
```

## 1. Initialize the Development Environment

Starting from version 0.3.0, Apollo-Chatchat supports pip-based installation and deployment. To avoid dependency version conflicts in the environment,
source code / development deployment no longer uses `requirements.txt` to manage project dependencies and instead switches to Poetry for environment management.

### 1.1 Install Poetry

> Before installing Poetry, if you are using Conda, please create and activate a new Conda environment, e.g., `conda create -n chatchat python=3.9`.

Install Poetry: [Poetry installation docs](https://python-poetry.org/docs/#installing-with-pipx)

> [!Note]
> If you do not have other projects that use Poetry for environment/dependency management, you can install Poetry using either pipx or pip.

> [!Note]
> If you use Conda or Pyenv as your environment/package manager, after installing Poetry,
> use the following command to make Poetry use the virtualenv python environment (`poetry config virtualenvs.prefer-active-python true`).

### 1.2 Install Dependencies for Source / Development Deployment

Enter the main project directory and install Apollo-Chatchat dependencies:

```shell
cd  Apollo-Chatchat/libs/apollo-chatchat-server/
poetry install --with lint,test -E xinference

# or use pip to install in editing mode:
pip install -e .
```

> [!Note]
> After running `poetry install`, a `chatchat-<version>.dist-info` folder containing a `direct_url.json` file will be generated under the `site-packages` path of your virtual environment. This file points to your development environment.

### 1.3 Update Dependencies in the Development Environment

When the dependencies required in the development environment change, the typical workflow is to first update `pyproject.toml` under the main project directory (`Apollo-Chatchat/libs/apollo-chatchat-server/`) and then run `poetry update`.

### 1.4 Package the Updated Code for Testing

If you need to package the code in the development environment into a Python library for testing, run the following command in the main project directory:

```shell
poetry build
```

After the command completes, a new `dist` directory will be created under the main project directory, which stores the packaged Python library.

## 2. Set the Source Code Root Directory

If the IDE you use for development requires you to specify the project source root directory, please set the main project directory (`Apollo-Chatchat/libs/apollo-chatchat-server/`) as the source root.

Before executing the following commands, please first set the current directory and project data directory:
```shell
cd Apollo-Chatchat/libs/apollo-chatchat-server/chatchat
export CHATCHAT_ROOT=/parth/to/chatchat_data
```

## 3. About chatchat Configuration

Starting from version `0.3.1`, all configuration items have been changed to `yaml` files. For details, see [Settings](settings.md).

Run the following commands to initialize the project configuration files and data directory:
```shell
cd libs/apollo-chatchat-server
python chatchat/cli.py init
```

## 4. Initialize the Knowledge Base

> [!WARNING]
> This command will clear the database and delete existing configuration files. Back up any important data first.

```shell
cd libs/apollo-chatchat-server
python chatchat/cli.py kb --recreate-vs
```
If you need to use a different Embedding model, or to rebuild a specific knowledge base, please refer to `python chatchat/cli.py kb --help` for more parameters.

## 5. Start the Service

```shell
cd libs/apollo-chatchat-server
python chatchat/cli.py start -a
```

To call the API, please refer to [API Usage Guide](api.md).
