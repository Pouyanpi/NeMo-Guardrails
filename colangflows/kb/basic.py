from typing import List

from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer

from colangflows.kb.index import EmbeddingsIndex, IndexItem


class BasicEmbeddingsIndex(EmbeddingsIndex):
    """Basic implementation of an embeddings index.

    It uses `sentence-transformers/all-MiniLM-L6-v2` to compute the embeddings.
    It uses Annoy to perform the search.
    """

    def __init__(self):
        self._model = None
        self._items = []
        self._embeddings = []
        self._index = None

    def _init_model(self):
        """Initialize the model used for computing the embeddings."""
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of texts."""
        if self._model is None:
            self._init_model()

        embeddings = self._model.encode(texts)
        return [embedding.tolist() for embedding in embeddings]

    def add_item(self, item: IndexItem):
        """Add a single item to the index."""
        self._items.append(item)
        self._embeddings.append(self._get_embeddings([item.text])[0])

    def add_items(self, items: List[IndexItem]):
        """Add multiple items to the index at once."""
        self._items.extend(items)
        self._embeddings.extend(self._get_embeddings([item.text for item in items]))

    def build(self):
        """Builds the Annoy index."""
        self._index = AnnoyIndex(len(self._embeddings[0]), "angular")
        for i in range(len(self._embeddings)):
            self._index.add_item(i, self._embeddings[i])
        self._index.build(10)

    def search(self, text: str, max_results: int = 20) -> List[IndexItem]:
        """Search the closest `max_results` items."""
        _embedding = self._get_embeddings([text])[0]
        results = self._index.get_nns_by_vector(
            _embedding,
            max_results,
        )

        return [self._items[i] for i in results]
