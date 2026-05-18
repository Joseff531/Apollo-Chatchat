
# Contributing Code
When contributing code to this repository, please follow the ["fork and pull request"](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) workflow unless you are a maintainer of the project. Please do not commit directly to the main branch.
Before submitting a PR, please follow the guidance in the pull request template. Note that our CI system automatically runs linting and tests to ensure that your code meets our standards.
More importantly, we need to maintain good unit tests and documentation. If you do any of the following, please:
- Add a new feature
Update the affected operation documentation
- Fix a bug
Add a unit test where possible, under tests/integration_tests or tests/unit_tests


## Dependency Management: Poetry and env/dependency Management
This project uses Poetry to manage dependencies.
> [!Note]
> Before installing Poetry, if you are using Conda, please create and activate a new Conda environment, e.g., `conda create -n chatchat python=3.9`.

Install Poetry: [Poetry installation docs](https://python-poetry.org/docs/#installing-with-pipx)

> [!Note]
> If you do not have other projects that use Poetry for environment/dependency management, you can install Poetry using either pipx or pip.

> [!Note]
> If you use Conda or Pyenv as your environment/package manager, after installing Poetry,
> use the following command to make Poetry use the virtualenv python environment (`poetry config virtualenvs.prefer-active-python true`).


## Installing the Local Development Environment

- Switch to the main project directory
```shell
cd  Apollo-Chatchat/libs/apollo-chatchat-server/
```

- Install chatchat dependencies (for running chatchat lint and tests):

```shell
poetry install --with lint,test
```
> After running `poetry install`, a `chatchat-<version>.dist-info` folder containing a `direct_url.json` file will be installed in your `site-packages`. This file points to your development environment.

## Formatting and Code Linting
Before submitting a PR, please run the following commands locally; the CI system will also perform these checks.

### Code Formatting
This project uses ruff for code formatting.

### About

To format a specific library, run the same command in its directory:
```shell
cd {apollo-chatchat-server|apollo-chatchat-frontend}
make format
```

In addition, you can use the `format_diff` command to format only the files modified in the current branch compared to the main branch:

```shell
make format_diff
```
This command is particularly useful when you have made changes to part of the project and want to ensure that the modified parts are properly formatted without affecting the rest of the codebase.

 
