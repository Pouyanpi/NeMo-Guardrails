import logging
from time import time
from typing import List

from collm.kb.basic import BasicEmbeddingsIndex
from collm.kb.index import IndexItem
from collm.kb.utils import split_markdown_in_topic_chunks

log = logging.getLogger(__name__)


class KnowledgeBase:
    """Basic implementation of a knowledge base."""

    def __init__(self, documents: List[str]):
        self.documents = documents
        self.chunks = []
        self.index = None

    def init(self):
        """Initialize the knowledge base.

        The initial data is loaded from the `$kb_docs` context key. The key is populated when
        the model is loaded. Currently, only markdown format is supported.
        """
        if not self.documents:
            return

        # Start splitting every doc into topic chunks

        for doc in self.documents:
            chunks = split_markdown_in_topic_chunks(doc)
            self.chunks.extend(chunks)

    def build(self):
        """Builds the knowledge base index."""
        t0 = time()
        index_items = []
        for chunk in self.chunks:
            text = f"# {chunk['title']}\n\n{chunk['body'].strip()}"

            index_items.append(IndexItem(text=text, meta=chunk))

        # Stop if there are no items
        if not index_items:
            return

        self.index = BasicEmbeddingsIndex()
        self.index.add_items(index_items)
        self.index.build()

        log.info(f"Building the Knowledge Base index took {time() - t0} seconds.")

    def search_relevant_chunks(self, text, max_results: int = 3):
        """Search the index for the most relevant chunks."""
        if self.index is None:
            return []

        results = self.index.search(text, max_results=max_results)

        # Return the chunks directly
        return [result.meta for result in results]
