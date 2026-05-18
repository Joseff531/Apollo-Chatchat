import json
import sys
from pathlib import Path

import requests

root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
from pprint import pprint

from chatchat.settings import Settings
from chatchat.server.knowledge_base.utils import get_file_path, get_kb_path
from chatchat.server.utils import api_address
from chatchat.webui_pages.utils import ApiRequest

api_base_url = api_address()
api: ApiRequest = ApiRequest(api_base_url)


kb = "kb_for_api_test"
test_files = {
    "FAQ.MD": str(root_path / "docs" / "FAQ.MD"),
    "README.MD": str(root_path / "README.MD"),
    "test.txt": get_file_path("samples", "test.txt"),
}

print("\n\nApiRequest invocation\n")


def test_delete_kb_before():
    if not Path(get_kb_path(kb)).exists():
        return

    data = api.delete_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]


def test_create_kb():
    print(f"\nTry creating a knowledge base with an empty name:")
    data = api.create_knowledge_base(" ")
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == "Knowledge base name cannot be empty, please re-enter the knowledge base name"

    print(f"\nCreate new knowledge base: {kb}")
    data = api.create_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 200
    assert data["msg"] == f"Knowledge base {kb} has been added"

    print(f"\nTry creating a duplicate knowledge base: {kb}")
    data = api.create_knowledge_base(kb)
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == f"A knowledge base with the same name already exists: {kb}"


def test_list_kbs():
    data = api.list_knowledge_bases()
    pprint(data)
    assert isinstance(data, list) and len(data) > 0
    assert kb in data


def test_upload_docs():
    files = list(test_files.values())

    print(f"\nUpload knowledge files")
    data = {"knowledge_base_name": kb, "override": True}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    print(f"\nUpload the same files again without overwrite")
    data = {"knowledge_base_name": kb, "override": False}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == len(test_files)

    print(f"\nUpload again with override + custom docs")
    docs = {"FAQ.MD": [{"page_content": "custom docs", "metadata": {}}]}
    data = {"knowledge_base_name": kb, "override": True, "docs": docs}
    data = api.upload_kb_docs(files, **data)
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_list_files():
    print("\nList files in the knowledge base:")
    data = api.list_kb_docs(knowledge_base_name=kb)
    pprint(data)
    assert isinstance(data, list)
    for name in test_files:
        assert name in data


def test_search_docs():
    query = "Tell me about the apollo-chatchat project"
    print("\nSearch the knowledge base:")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == Settings.kb_settings.VECTOR_SEARCH_TOP_K


def test_update_docs():
    print(f"\nUpdate knowledge files")
    data = api.update_kb_docs(knowledge_base_name=kb, file_names=list(test_files))
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_delete_docs():
    print(f"\nDelete knowledge files")
    data = api.delete_kb_docs(knowledge_base_name=kb, file_names=list(test_files))
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    query = "Tell me about the apollo-chatchat project"
    print("\nSearch the knowledge base after deletion:")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == 0


def test_recreate_vs():
    print("\nRebuild the knowledge base:")
    r = api.recreate_vector_store(kb)
    for data in r:
        assert isinstance(data, dict)
        assert data["code"] == 200
        print(data["msg"])

    query = "What file formats does this project support?"
    print("\nSearch the rebuilt knowledge base:")
    print(query)
    data = api.search_kb_docs(query, kb)
    pprint(data)
    assert isinstance(data, list) and len(data) == Settings.kb_settings.VECTOR_SEARCH_TOP_K


def test_delete_kb_after():
    print("\nDelete knowledge base")
    data = api.delete_knowledge_base(kb)
    pprint(data)

    # check kb not exists anymore
    print("\nList knowledge bases:")
    data = api.list_knowledge_bases()
    pprint(data)
    assert isinstance(data, list) and len(data) > 0
    assert kb not in data
