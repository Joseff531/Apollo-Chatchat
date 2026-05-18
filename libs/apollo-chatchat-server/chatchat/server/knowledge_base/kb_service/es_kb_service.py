import logging
import os
import shutil
from typing import List

from elasticsearch import BadRequestError, Elasticsearch
from langchain.schema import Document
from langchain_community.vectorstores.elasticsearch import (
    ApproxRetrievalStrategy,
    ElasticsearchStore,
)

from chatchat.settings import Settings
from chatchat.server.file_rag.utils import get_Retriever
from chatchat.server.knowledge_base.kb_service.base import KBService, SupportedVSType
from chatchat.server.knowledge_base.utils import KnowledgeFile
from chatchat.server.utils import get_Embeddings
from chatchat.utils import build_logger


logger = build_logger()


class ESKBService(KBService):
    def do_init(self):
        self.kb_path = self.get_kb_path(self.kb_name)
        self.index_name = os.path.split(self.kb_path)[-1]
        kb_config = Settings.kb_settings.kbs_config[self.vs_type()]
        self.scheme = kb_config.get("scheme", "http")
        self.IP = kb_config["host"]
        self.PORT = kb_config["port"]
        self.user = kb_config.get("user", "")
        self.password = kb_config.get("password", "")
        self.verify_certs = kb_config.get("verify_certs", True)
        self.ca_certs = kb_config.get("ca_certs", None)
        self.client_key = kb_config.get("client_key", None)
        self.client_cert = kb_config.get("client_cert", None)
        self.dims_length = kb_config.get("dims_length", None)
        self.embeddings_model = get_Embeddings(self.embed_model)
        try:
            connection_info = dict(
                host=f"{self.scheme}://{self.IP}:{self.PORT}"
            )
            if self.user != "" and self.password != "":
                connection_info.update(basic_auth=(self.user, self.password))
            else:
                logger.warning("ES username and password are not configured")
            if self.scheme == "https":
                connection_info.update(verify_certs=self.verify_certs)
                if self.ca_certs:
                    connection_info.update(ca_certs=self.ca_certs)
                if self.client_key and self.client_cert:
                    connection_info.update(client_key=self.client_key)
                    connection_info.update(client_cert=self.client_cert)
            # ES python client connection (connection only)
            self.es_client_python = Elasticsearch(**connection_info)
        except ConnectionError:
            logger.error("Failed to connect to Elasticsearch!")
            raise ConnectionError
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            raise e
        try:
            # First try to create via es_client_python
            mappings = {
                "properties": {
                    "dense_vector": {
                        "type": "dense_vector",
                        "dims": self.dims_length,
                        "index": True,
                    }
                }
            }
            self.es_client_python.indices.create(
                index=self.index_name, mappings=mappings
            )
        except BadRequestError as e:
            logger.error("Failed to create index, retrying")
            logger.error(e)

        try:
            # langchain ES connection and index creation
            params = dict(
                es_url=f"{self.scheme}://{self.IP}:{self.PORT}",
                index_name=self.index_name,
                query_field="context",
                vector_query_field="dense_vector",
                embedding=self.embeddings_model,
                strategy=ApproxRetrievalStrategy(),
                es_params={
                    "timeout": 60,
                },
            )
            if self.user != "" and self.password != "":
                params.update(es_user=self.user, es_password=self.password)
            if self.scheme == "https":
                params["es_params"].update(verify_certs=self.verify_certs)
                if self.ca_certs:
                    params["es_params"].update(ca_certs=self.ca_certs)
                if self.client_key and self.client_cert:
                    params["es_params"].update(client_key=self.client_key)
                    params["es_params"].update(client_cert=self.client_cert)
            self.db = ElasticsearchStore(**params)
        except ConnectionError:
            logger.error("### Failed to initialize Elasticsearch!")
            raise ConnectionError
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            raise e
        try:
            # Try to create the index via db_init
            self.db._create_index_if_not_exists(
                index_name=self.index_name, dims_length=self.dims_length
            )
        except Exception as e:
            logger.error("Failed to create index...")
            logger.error(e)
            # raise e

    @staticmethod
    def get_kb_path(knowledge_base_name: str):
        return os.path.join(Settings.basic_settings.KB_ROOT_PATH, knowledge_base_name)

    @staticmethod
    def get_vs_path(knowledge_base_name: str):
        return os.path.join(
            ESKBService.get_kb_path(knowledge_base_name), "vector_store"
        )

    def do_create_kb(self):
        ...

    def vs_type(self) -> str:
        return SupportedVSType.ES

    def do_search(self, query: str, top_k: int, score_threshold: float):
        # Text similarity search
        retriever = get_Retriever("vectorstore").from_vectorstore(
            self.db,
            top_k=top_k,
            score_threshold=score_threshold,
        )
        docs = retriever.get_relevant_documents(query)
        return docs

    def get_doc_by_ids(self, ids: List[str]) -> List[Document]:
        results = []
        for doc_id in ids:
            try:
                response = self.es_client_python.get(index=self.index_name, id=doc_id)
                source = response["_source"]
                # Assuming your document has "text" and "metadata" fields
                text = source.get("context", "")
                metadata = source.get("metadata", {})
                results.append(Document(page_content=text, metadata=metadata))
            except Exception as e:
                logger.error(f"Error retrieving document from Elasticsearch! {e}")
        return results

    def del_doc_by_ids(self, ids: List[str]) -> bool:
        for doc_id in ids:
            try:
                self.es_client_python.delete(
                    index=self.index_name, id=doc_id, refresh=True
                )
            except Exception as e:
                logger.error(f"ES Docs Delete Error! {e}")

    def do_delete_doc(self, kb_file, **kwargs):
        if self.es_client_python.indices.exists(index=self.index_name):
            # Delete index from the vector database (document name is a Keyword)
            query = {
                "query": {
                    "term": {
                        "metadata.source.keyword": self.get_relative_source_path(
                            kb_file.filepath
                        )
                    }
                },
                "track_total_hits": True,
            }
            # Note the size setting; defaults to 10. Setting track_total_hits to True returns the real size in the database.
            size = self.es_client_python.search(body=query)["hits"]["total"]["value"]
            search_results = self.es_client_python.search(body=query, size=size)
            delete_list = [hit["_id"] for hit in search_results["hits"]["hits"]]
            if len(delete_list) == 0:
                return None
            else:
                for doc_id in delete_list:
                    try:
                        self.es_client_python.delete(
                            index=self.index_name, id=doc_id, refresh=True
                        )
                    except Exception as e:
                        logger.error(f"ES Docs Delete Error! {e}")

            # self.db.delete(ids=delete_list)
            # self.es_client_python.indices.refresh(index=self.index_name)

    def do_add_doc(self, docs: List[Document], **kwargs):
        """Add files to the knowledge base"""

        print(
            f"server.knowledge_base.kb_service.es_kb_service.do_add_doc input docs length: {len(docs)}"
        )
        print("*" * 100)

        self.db.add_documents(documents=docs)
        # Retrieve id and source, format: [{"id": str, "metadata": dict}, ...]
        print("Data written successfully.")
        print("*" * 100)

        if self.es_client_python.indices.exists(index=self.index_name):
            file_path = docs[0].metadata.get("source")
            query = {
                "query": {
                    "term": {"metadata.source.keyword": file_path},
                    "term": {"_index": self.index_name},
                }
            }
            # Note the size setting; defaults to 10.
            search_results = self.es_client_python.search(body=query, size=50)
            if len(search_results["hits"]["hits"]) == 0:
                raise ValueError("Number of retrieved elements is 0")
            info_docs = [
                {"id": hit["_id"], "metadata": hit["_source"]["metadata"]}
                for hit in search_results["hits"]["hits"]
            ]
            return info_docs

    def do_clear_vs(self):
        """Delete all vectors from the knowledge base"""
        if self.es_client_python.indices.exists(index=self.kb_name):
            self.es_client_python.indices.delete(index=self.kb_name)

    def do_drop_kb(self):
        """Delete the knowledge base"""
        # self.kb_file: knowledge base path
        if os.path.exists(self.kb_path):
            shutil.rmtree(self.kb_path)


if __name__ == "__main__":
    esKBService = ESKBService("test")
    # esKBService.clear_vs()
    # esKBService.create_kb()
    esKBService.add_doc(KnowledgeFile(filename="README.md", knowledge_base_name="test"))
    print(esKBService.search_docs("How to start the api service"))
