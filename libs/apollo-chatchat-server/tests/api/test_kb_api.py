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

api_base_url = api_address()


kb = "kb_for_api_test"
test_files = {
    "wiki/Home.MD": get_file_path("samples", "wiki/Home.md"),
    "wiki/dev_environment_setup.MD": get_file_path("samples", "wiki/dev_environment_setup.md"),
    "test_files/test.txt": get_file_path("samples", "test_files/test.txt"),
}

print("\n\nDirect URL access\n")


def test_delete_kb_before(api="/knowledge_base/delete_knowledge_base"):
    if not Path(get_kb_path(kb)).exists():
        return

    url = api_base_url + api
    print("\nKnowledge base already exists, deleting...")
    r = requests.post(url, json=kb)
    data = r.json()
    pprint(data)

    # check kb not exists anymore
    url = api_base_url + "/knowledge_base/list_knowledge_bases"
    print("\nList knowledge bases:")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]


def test_create_kb(api="/knowledge_base/create_knowledge_base"):
    url = api_base_url + api

    print(f"\nTry creating a knowledge base with an empty name:")
    r = requests.post(url, json={"knowledge_base_name": " "})
    data = r.json()
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == "Knowledge base name cannot be empty, please re-enter the knowledge base name"

    print(f"\nCreate new knowledge base: {kb}")
    r = requests.post(url, json={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert data["msg"] == f"Knowledge base {kb} has been added"

    print(f"\nTry creating a duplicate knowledge base: {kb}")
    r = requests.post(url, json={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 404
    assert data["msg"] == f"A knowledge base with the same name already exists: {kb}"


def test_list_kbs(api="/knowledge_base/list_knowledge_bases"):
    url = api_base_url + api
    print("\nList knowledge bases:")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb in data["data"]


def test_upload_docs(api="/knowledge_base/upload_docs"):
    url = api_base_url + api
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]

    print(f"\nUpload knowledge files")
    data = {"knowledge_base_name": kb, "override": True}
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    print(f"\nUpload the same files again without overwrite")
    data = {"knowledge_base_name": kb, "override": False}
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == len(test_files)

    print(f"\nUpload again with override + custom docs")
    docs = {"FAQ.MD": [{"page_content": "custom docs", "metadata": {}}]}
    data = {"knowledge_base_name": kb, "override": True, "docs": json.dumps(docs)}
    files = [("files", (name, open(path, "rb"))) for name, path in test_files.items()]
    r = requests.post(url, data=data, files=files)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_list_files(api="/knowledge_base/list_files"):
    url = api_base_url + api
    print("\nList files in the knowledge base:")
    r = requests.get(url, params={"knowledge_base_name": kb})
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list)
    for name in test_files:
        assert name in data["data"]


def test_search_docs(api="/knowledge_base/search_docs"):
    url = api_base_url + api
    query = "Tell me about the apollo-chatchat project"
    print("\nSearch the knowledge base:")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == Settings.kb_settings.VECTOR_SEARCH_TOP_K


def test_update_info(api="/knowledge_base/update_info"):
    url = api_base_url + api
    print("\nUpdate knowledge-base description")
    r = requests.post(url, json={"knowledge_base_name": "samples", "kb_info": "hello"})
    data = r.json()
    pprint(data)
    assert data["code"] == 200


def test_update_docs(api="/knowledge_base/update_docs"):
    url = api_base_url + api

    print(f"\nUpdate knowledge files")
    r = requests.post(
        url, json={"knowledge_base_name": kb, "file_names": list(test_files)}
    )
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0


def test_delete_docs(api="/knowledge_base/delete_docs"):
    url = api_base_url + api

    print(f"\nDelete knowledge files")
    r = requests.post(
        url, json={"knowledge_base_name": kb, "file_names": list(test_files)}
    )
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert len(data["data"]["failed_files"]) == 0

    url = api_base_url + "/knowledge_base/search_docs"
    query = "Tell me about the apollo-chatchat project"
    print("\nSearch the knowledge base after deletion:")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == 0


def test_recreate_vs(api="/knowledge_base/recreate_vector_store"):
    url = api_base_url + api
    print("\nRebuild the knowledge base:")
    r = requests.post(url, json={"knowledge_base_name": kb}, stream=True)
    for chunk in r.iter_content(None):
        data = json.loads(chunk[6:])
        assert isinstance(data, dict)
        assert data["code"] == 200
        print(data["msg"])

    url = api_base_url + "/knowledge_base/search_docs"
    query = "What file formats does this project support?"
    print("\nSearch the rebuilt knowledge base:")
    print(query)
    r = requests.post(url, json={"knowledge_base_name": kb, "query": query})
    data = r.json()
    pprint(data)
    assert isinstance(data, list) and len(data) == Settings.kb_settings.VECTOR_SEARCH_TOP_K


def test_delete_kb_after(api="/knowledge_base/delete_knowledge_base"):
    url = api_base_url + api
    print("\nDelete knowledge base")
    r = requests.post(url, json=kb)
    data = r.json()
    pprint(data)

    # check kb not exists anymore
    url = api_base_url + "/knowledge_base/list_knowledge_bases"
    print("\nList knowledge bases:")
    r = requests.get(url)
    data = r.json()
    pprint(data)
    assert data["code"] == 200
    assert isinstance(data["data"], list) and len(data["data"]) > 0
    assert kb not in data["data"]
