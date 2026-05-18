from langchain.docstore.document import Document


class DocumentWithVSId(Document):
    """
    Document after vectorization
    """

    id: str = None
    score: float = 3.0
