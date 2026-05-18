from langchain.chains import LLMChain
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts.prompt import PromptTemplate
from langchain_experimental.sql import SQLDatabaseChain, SQLDatabaseSequentialChain
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from chatchat.server.pydantic_v1 import Field
from chatchat.server.utils import get_tool_config

from .tools_registry import regist_tool

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)

READ_ONLY_PROMPT_TEMPLATE = """You are a MySQL expert. The database is currently in read-only mode. 
Given an input question, determine if the related SQL can be executed in read-only mode.
If the SQL can be executed normally, return Answer:'SQL can be executed normally'.
If the SQL cannot be executed normally, return Answer: 'SQL cannot be executed normally'.
Use the following format:

Answer: Final answer here

Question: {query}
"""


# Define an interceptor function to inspect SQL statements for read-only support.
# You can modify the write_operations list below to match the write keywords of the database you use.
def intercept_sql(conn, cursor, statement, parameters, context, executemany):
    # List of SQL keywords that indicate a write operation
    write_operations = (
        "insert",
        "update",
        "delete",
        "create",
        "drop",
        "alter",
        "truncate",
        "rename",
    )
    # Check if the statement starts with any of the write operation keywords
    if any(statement.strip().lower().startswith(op) for op in write_operations):
        raise OperationalError(
            "Database is read-only. Write operations are not allowed.",
            params=None,
            orig=None,
        )


def query_database(query: str, config: dict):
    model_name= config["model_name"]
    top_k = config["top_k"]
    return_intermediate_steps = config["return_intermediate_steps"]
    sqlalchemy_connect_str = config["sqlalchemy_connect_str"]
    read_only = config["read_only"]
    db = SQLDatabase.from_uri(sqlalchemy_connect_str)

    from chatchat.server.utils import get_ChatOpenAI

    llm = get_ChatOpenAI(
        model_name=model_name,
        temperature=0.1,
        streaming=True,
        local_wrap=True,
        verbose=True,
    )
    table_names = config["table_names"]
    table_comments = config["table_comments"]
    result = None

    # If the LLM has trouble deciding which tables to use, try giving langchain extra table descriptions
    # to help the LLM pick the correct tables. This matters especially under SQLDatabaseSequentialChain,
    # which predicts by table name and is easy to get wrong.
    # Because langchain's input parameters are fixed, the only way to pass extra table notes is through the query.
    if table_comments:
        TABLE_COMMNET_PROMPT = (
            "\n\nI will provide some special notes for a few tables:\n\n"
        )
        table_comments_str = "\n".join([f"{k}:{v}" for k, v in table_comments.items()])
        query = query + TABLE_COMMNET_PROMPT + table_comments_str + "\n\n"

    if read_only:
        # Under read_only mode, first ask the LLM to determine whether read-only can satisfy the request,
        # so we avoid runtime errors later and return a friendly message instead.
        READ_ONLY_PROMPT = PromptTemplate(
            input_variables=["query"],
            template=READ_ONLY_PROMPT_TEMPLATE,
        )
        read_only_chain = LLMChain(
            prompt=READ_ONLY_PROMPT,
            llm=llm,
        )
        read_only_result = read_only_chain.invoke(query)
        if "SQL cannot be executed normally" in read_only_result["text"]:
            return "The database is currently read-only and cannot satisfy your request!"

        # The LLM judgement cannot be guaranteed accurate, so also reject write operations at the interceptor level.
        event.listen(db._engine, "before_cursor_execute", intercept_sql)

    # If table_names is not specified, prefer SQLDatabaseSequentialChain, which first predicts which tables are needed
    # and then feeds the relevant tables into SQLDatabaseChain.
    # This is because without table_names, going straight to SQLDatabaseChain would have Langchain pass the entire schema
    # to the LLM, which may exceed the token limit and waste resources.
    # If table_names is specified, go straight to SQLDatabaseChain and pass only the specified table schema to the LLM.
    if len(table_names) > 0:
        db_chain = SQLDatabaseChain.from_llm(
            llm,
            db,
            verbose=True,
            top_k=top_k,
            return_intermediate_steps=return_intermediate_steps,
        )
        result = db_chain.invoke({"query": query, "table_names_to_use": table_names})
    else:
        # First predict which tables will be used, then give the question and the predicted tables to the LLM.
        db_chain = SQLDatabaseSequentialChain.from_llm(
            llm,
            db,
            verbose=True,
            top_k=top_k,
            return_intermediate_steps=return_intermediate_steps,
        )
        result = db_chain.invoke(query)

    context = f"""Query result: {result['result']}\n\n"""

    intermediate_steps = result["intermediate_steps"]
    # If intermediate_steps exists and the list length is greater than 2, keep only the last two entries,
    # because the earlier steps include sample data that can be misleading.
    if intermediate_steps:
        if len(intermediate_steps) > 2:
            sql_detail = intermediate_steps[-2:-1][0]["input"]
            # Slice sql_detail to keep just the content between SQLQuery: and Answer:.
            sql_detail = sql_detail[
                sql_detail.find("SQLQuery:") + 9 : sql_detail.find("Answer:")
            ]
            context = context + "Executed SQL: '" + sql_detail + "'\n\n"
    return context


@regist_tool(title="Database Chat")
def text2sql(
    query: str = Field(
        description="No need for SQL statements,just input the natural language that you want to chat with database"
    ),
):
    """Use this tool to chat with  database,Input natural language, then it will convert it into SQL and execute it in the database, then return the execution result."""
    tool_config = get_tool_config("text2sql")
    return BaseToolOutput(query_database(query=query, config=tool_config))
