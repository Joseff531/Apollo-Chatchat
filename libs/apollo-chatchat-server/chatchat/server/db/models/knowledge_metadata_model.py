from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, func

from chatchat.server.db.base import Base


class SummaryChunkModel(Base):
    """
    Chunk summary model. Stores chunk fragments associated with each doc_id in file_doc.
    Data sources:
        User input: when uploading a file, the user can provide a description; the doc_id
            generated in file_doc is stored in summary_chunk together with it.
        Automatic splitting: the page-number information stored in the meta_data field of
            the file_doc table is used to split per page, a custom prompt generates summary
            text, and the doc_id associated with each page is stored in summary_chunk.
    Downstream tasks:
        Vector store construction: build an index on the summary_context column of the
            summary_chunk table and construct a vector store, with meta_data (doc_ids) as
            the vector store metadata.
        Semantic linking: compute semantic similarity between the user-supplied description
            and the automatically split summary text.

    """

    __tablename__ = "summary_chunk"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    kb_name = Column(String(50), comment="Knowledge base name")
    summary_context = Column(String(255), comment="Summary text")
    summary_id = Column(String(255), comment="Summary vector id")
    doc_ids = Column(String(1024), comment="List of associated vector store ids")
    meta_data = Column(JSON, default={})

    def __repr__(self):
        return (
            f"<SummaryChunk(id='{self.id}', kb_name='{self.kb_name}', summary_context='{self.summary_context}',"
            f" doc_ids='{self.doc_ids}', metadata='{self.metadata}')>"
        )
