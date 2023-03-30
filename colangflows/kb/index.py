from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IndexItem:
    text: str
    meta: Dict = field(default_factory=dict)


class EmbeddingsIndex:
    """The embeddings index is responsible for computing and searching a set of embeddings."""

    def add_item(self, item: IndexItem):
        """Adds a new item to the index."""
        raise NotImplementedError()

    def add_items(self, item: List[IndexItem]):
        """Adds multiple items to the index."""
        raise NotImplementedError()

    def build(self):
        """Build the index, after the items are added.

        This is optional, might not be needed for all implementations."""
        pass

    def search(self, text: str, max_results: int) -> List[IndexItem]:
        """Searches the index for the closes matches to the provided text."""
        raise NotImplementedError()
