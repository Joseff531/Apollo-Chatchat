import asyncio
import logging
import sys
from typing import List, Optional

from langchain.chains import LLMChain, StuffDocumentsChain
from langchain.chains.combine_documents.map_reduce import (
    MapReduceDocumentsChain,
    ReduceDocumentsChain,
)
from langchain.docstore.document import Document
from langchain.output_parsers.regex import RegexParser
from langchain.prompts import PromptTemplate
from langchain.schema.language_model import BaseLanguageModel

from chatchat.server.knowledge_base.model.kb_document_model import DocumentWithVSId
from chatchat.utils import build_logger


logger = build_logger()


class SummaryAdapter:
    _OVERLAP_SIZE: int
    token_max: int
    _separator: str = "\n\n"
    chain: MapReduceDocumentsChain

    def __init__(
        self, overlap_size: int, token_max: int, chain: MapReduceDocumentsChain
    ):
        self._OVERLAP_SIZE = overlap_size
        self.chain = chain
        self.token_max = token_max

    @classmethod
    def form_summary(
        cls,
        llm: BaseLanguageModel,
        reduce_llm: BaseLanguageModel,
        overlap_size: int,
        token_max: int = 1300,
    ):
        """
        Get an instance
        :param reduce_llm: the llm used to merge summaries
        :param llm: the llm used to generate summaries
        :param overlap_size: size of the overlap
        :param token_max: maximum number of chunks; each chunk must be shorter than token_max; summaries longer than token_max will raise an error during the first summary generation
        :return:
        """

        # This controls how each document will be formatted. Specifically,
        document_prompt = PromptTemplate(
            input_variables=["page_content"], template="{page_content}"
        )

        # The prompt here should take as an input variable the
        # `document_variable_name`
        prompt_template = (
            "Perform the task based on the text. Task information is as follows:"
            "{task_briefing}"
            "The text content is as follows: "
            "\r\n"
            "{context}"
        )
        prompt = PromptTemplate(
            template=prompt_template, input_variables=["task_briefing", "context"]
        )
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        # We now define how to combine these summaries
        reduce_prompt = PromptTemplate.from_template(
            "Combine these summaries: {context}"
        )
        reduce_llm_chain = LLMChain(llm=reduce_llm, prompt=reduce_prompt)

        document_variable_name = "context"
        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_llm_chain,
            document_prompt=document_prompt,
            document_variable_name=document_variable_name,
        )
        reduce_documents_chain = ReduceDocumentsChain(
            token_max=token_max,
            combine_documents_chain=combine_documents_chain,
        )
        chain = MapReduceDocumentsChain(
            llm_chain=llm_chain,
            document_variable_name=document_variable_name,
            reduce_documents_chain=reduce_documents_chain,
            # Return intermediate steps
            return_intermediate_steps=True,
        )
        return cls(overlap_size=overlap_size, chain=chain, token_max=token_max)

    def summarize(
        self, file_description: str, docs: List[DocumentWithVSId] = []
    ) -> List[Document]:
        if sys.version_info < (3, 10):
            loop = asyncio.get_event_loop()
        else:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)
        # Call the coroutine synchronously
        return loop.run_until_complete(
            self.asummarize(file_description=file_description, docs=docs)
        )

    async def asummarize(
        self, file_description: str, docs: List[DocumentWithVSId] = []
    ) -> List[Document]:
        logger.info("start summary")
        """
        This process is split into two parts:
        1. Process each document to obtain its summary
         map_results = self.llm_chain.apply(
            # FYI - this is parallelized and so it is fast.
            [{self.document_variable_name: d.page_content, **kwargs} for d in docs],
            callbacks=callbacks,
        )
        2. Merge the summaries of each document to obtain the final summary; return_intermediate_steps=True returns the intermediate steps
        result, extra_return_dict = self.reduce_documents_chain.combine_docs(
            result_docs, token_max=token_max, callbacks=callbacks, **kwargs
        )
        """
        summary_combine, summary_intermediate_steps = self.chain.combine_docs(
            docs=docs,
            task_briefing="Describe the closeness and similarity between different methods "
            "to help readers understand the relationships among them.",
        )
        print(summary_combine)
        print(summary_intermediate_steps)

        # if len(summary_combine) == 0:
        #     # If empty, regenerate with half the count
        #     result_docs = [
        #         Document(page_content=question_result_key, metadata=docs[i].metadata)
        #         # This uses metadata from the docs, and the textual results from `results`
        #         for i, question_result_key in enumerate(
        #             summary_intermediate_steps["intermediate_steps"][
        #             :len(summary_intermediate_steps["intermediate_steps"]) // 2
        #             ])
        #     ]
        #     summary_combine, summary_intermediate_steps = self.chain.reduce_documents_chain.combine_docs(
        #         result_docs, token_max=self.token_max
        #     )
        logger.info("end summary")
        doc_ids = ",".join([doc.id for doc in docs])
        _metadata = {
            "file_description": file_description,
            "summary_intermediate_steps": summary_intermediate_steps,
            "doc_ids": doc_ids,
        }
        summary_combine_doc = Document(page_content=summary_combine, metadata=_metadata)

        return [summary_combine_doc]

    def _drop_overlap(self, docs: List[DocumentWithVSId]) -> List[str]:
        """
         # Remove the overlapping sentence portions in page_content across documents
        :param docs:
        :param separator:
        :return:
        """
        merge_docs = []

        pre_doc = None
        for doc in docs:
            # Add the first document directly
            if len(merge_docs) == 0:
                pre_doc = doc.page_content
                merge_docs.append(doc.page_content)
                continue

            # For the overlapping portion between the end of the previous and the start of the next, remove the overlap at the start of the next
            # Iteratively decrease the length of pre_doc, removing the leading character each iteration,
            # and check for an overlap until pre_doc length is less than self._OVERLAP_SIZE // 2 - 2*len(separator)
            for i in range(
                len(pre_doc), self._OVERLAP_SIZE // 2 - 2 * len(self._separator), -1
            ):
                # Remove the leading character each iteration
                pre_doc = pre_doc[1:]
                if doc.page_content[: len(pre_doc)] == pre_doc:
                    # Remove the overlapping portion at the start of the next document
                    merge_docs.append(doc.page_content[len(pre_doc) :])
                    break

            pre_doc = doc.page_content

        return merge_docs

    def _join_docs(self, docs: List[str]) -> Optional[str]:
        text = self._separator.join(docs)
        text = text.strip()
        if text == "":
            return None
        else:
            return text


if __name__ == "__main__":
    docs = [
        "The dreamer has a special role; that is, dreams foretell the future. Therefore, the dream content",
        "The colorful nature of dream content and the special impressions it leaves on the dreamer make it hard to imagine",
        "make it hard to imagine a unified system of ideas, requiring instead various",
        "various divisions and aggregations based on their individual value and reliability. Hence, the ancient philosophers' evaluations of dreams were entirely",
    ]
    _OVERLAP_SIZE = 1
    separator: str = "\n\n"
    merge_docs = []
    # Remove the overlapping sentence portions in page_content across documents;
    # for the overlap between the end of the previous and the start of the next, remove the overlap at the start of the next
    pre_doc = None
    for doc in docs:
        # Add the first document directly
        if len(merge_docs) == 0:
            pre_doc = doc
            merge_docs.append(doc)
            continue

        # For the overlap between the end of the previous and the start of the next, remove the overlap at the start of the next
        # Iteratively decrease the length of pre_doc, removing the leading character each iteration,
        # and check for an overlap until pre_doc length is less than _OVERLAP_SIZE - 2*len(separator)
        for i in range(len(pre_doc), _OVERLAP_SIZE - 2 * len(separator), -1):
            # Remove the leading character each iteration
            pre_doc = pre_doc[1:]
            if doc[: len(pre_doc)] == pre_doc:
                # Remove the overlapping portion at the start of the next document
                page_content = doc[len(pre_doc) :]
                merge_docs.append(page_content)

                pre_doc = doc
                break

    # Merge the sentences in merge_docs into a single document
    text = separator.join(merge_docs)
    text = text.strip()

    print(text)
