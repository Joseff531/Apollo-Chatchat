import click
from pathlib import Path
import shutil
import typing as t

from chatchat.startup import main as startup_main
from chatchat.init_database import main as kb_main, create_tables, folder2db
from chatchat.settings import Settings
from chatchat.utils import build_logger
from chatchat.server.utils import get_default_embedding


logger = build_logger()


@click.group(help="chatchat command line tool")
def main():
    ...


@main.command("init", help="Initialize the project")
@click.option("-x", "--xinference-endpoint", "xf_endpoint",
              help="Specify the Xinference API endpoint. Defaults to http://127.0.0.1:9997/v1")
@click.option("-l", "--llm-model",
              help="Specify the default LLM model. Defaults to glm4-chat")
@click.option("-e", "--embed-model",
              help="Specify the default Embedding model. Defaults to bge-large-zh-v1.5")
@click.option("-r", "--recreate-kb",
              is_flag=True,
              show_default=True,
              default=False,
              help="Also rebuild the knowledge base (make sure the specified embed model is available).")
@click.option("-k", "--kb-names", "kb_names",
              show_default=True,
              default="samples",
              help="Names of knowledge bases to rebuild. Multiple names can be provided, separated by commas.")
def init(
    xf_endpoint: str = "",
    llm_model: str = "",
    embed_model: str = "",
    recreate_kb: bool = False,
    kb_names: str = "",
):
    Settings.set_auto_reload(False)
    bs = Settings.basic_settings
    kb_names = [x.strip() for x in kb_names.split(",")]
    logger.success(f"Initializing project data directory: {Settings.CHATCHAT_ROOT}")
    Settings.basic_settings.make_dirs()
    logger.success("Created all data directories: success.")
    if(bs.PACKAGE_ROOT / "data/knowledge_base/samples" != Path(bs.KB_ROOT_PATH) / "samples"):
        shutil.copytree(bs.PACKAGE_ROOT / "data/knowledge_base/samples", Path(bs.KB_ROOT_PATH) / "samples", dirs_exist_ok=True)
    logger.success("Copied samples knowledge base files: success.")
    create_tables()
    logger.success("Initialized knowledge base database: success.")

    if xf_endpoint:
        Settings.model_settings.MODEL_PLATFORMS[0].api_base_url = xf_endpoint
    if llm_model:
        Settings.model_settings.DEFAULT_LLM_MODEL = llm_model
    if embed_model:
        Settings.model_settings.DEFAULT_EMBEDDING_MODEL = embed_model

    Settings.createl_all_templates()
    Settings.set_auto_reload(True)

    logger.success("Generated default configuration files: success.")
    logger.success("Please verify that the model platforms, LLM model, and Embed model information in model_settings.yaml are correct")

    if recreate_kb:
        folder2db(kb_names=kb_names,
                  mode="recreate_vs",
                  vs_type=Settings.kb_settings.DEFAULT_VS_TYPE,
                  embed_model=get_default_embedding())
        logger.success("<green>All initialization completed. Run 'chatchat start -a' to start the service.</green>")
    else:
        logger.success("Run 'chatchat kb -r' to initialize the knowledge base, then 'chatchat start -a' to start the service.")


main.add_command(startup_main, "start")
main.add_command(kb_main, "kb")


if __name__ == "__main__":
    main()
