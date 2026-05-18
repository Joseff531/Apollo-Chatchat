import re
from typing import List

from langchain.text_splitter import CharacterTextSplitter


class AliTextSplitter(CharacterTextSplitter):
    def __init__(self, pdf: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.pdf = pdf

    def split_text(self, text: str) -> List[str]:
        # The `use_document_segmentation` argument controls whether to segment the document semantically. The model used here for document-level semantic segmentation is DAMO Academy's open-source nlp_bert_document-segmentation_chinese-base; see the paper at https://arxiv.org/abs/2107.09278
        # To use the model for semantic document segmentation, install modelscope[nlp]: pip install "modelscope[nlp]" -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
        # Because three models are used, this may not be friendly to low-spec GPUs; therefore the model is loaded onto the CPU for inference here. Replace `device` with your own GPU id if needed.
        if self.pdf:
            text = re.sub(r"\n{3,}", r"\n", text)
            text = re.sub("\s", " ", text)
            text = re.sub("\n\n", "", text)
        try:
            from modelscope.pipelines import pipeline
        except ImportError:
            raise ImportError(
                "Could not import modelscope python package. "
                "Please install modelscope with `pip install modelscope`. "
            )

        p = pipeline(
            task="document-segmentation",
            model="damo/nlp_bert_document-segmentation_chinese-base",
            device="cpu",
        )
        result = p(documents=text)
        sent_list = [i for i in result["text"].split("\n\t") if i]
        return sent_list
