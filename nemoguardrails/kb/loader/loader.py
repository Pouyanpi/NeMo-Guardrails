from typing import Any, Callable, Iterable, List

from pydantic import BaseModel

from unstructured.partition.html import partition_html
from unstructured.documents.elements import Element
from unstructured.documents.elements import Text
from unstructured.documents.elements import FigureCaption
from unstructured.documents.elements import NarrativeText
from unstructured.documents.elements import ListItem
from unstructured.documents.elements import Title
from unstructured.documents.elements import Address
from unstructured.documents.elements import Image
from unstructured.documents.elements import PageBreak
from unstructured.documents.elements import Table



class Document(BaseModel):
    content: str
    type: str
    format: str
    metadata: Dict[str, Any] = {}
    file_path: str
    loader: str

class Topic(BaseModel):
    title: str
    body: str
    metadata: Dict[str, Any] = {}     


class DocumentLoader(ABC):
    """Abstract class for loaders.
    
    :param file_path: The path to the file to load.
    :type file_path: str
    :param partition_handler: The partition handler to use.
    :type partition_handler: Callable
    :param kwargs: Keyword arguments to pass to the partition handler.
    :type kwargs: Any

    Example:
        >>> from nemoguardrails.kb.loaders import DocumentLoader
        >>> loader = DocumentLoader(file_path="path/to/file.md")
        >>> for document in loader.load():
        ...     print(document.content)
        ...     print(document.type)
        ...     print(document.format)
        ...     print(document.metadata)
        ...     print(document.file_path)
        ...     print(document.loader)

        
    
    
    """
    def __init__(self, file_path: partition_handler: Callable = None , str, **kwargs: Any):
        """Initialize a DocumentLoader."""
        self.file_path = file_path
        self._kwargs = kwargs
        self._partition_handler = None

    @property
    def partition_handler(self):
        if self._partition_handler is None:
            self._partition_handler = self._get_partition_handler()
        return self._partition_handler(**self._kwargs)

    def _get_partition_handler(self):
        """Get the partition handler for the loader."""

        return PartitionFactory.get_partition_function(detect_filetype(self.file_path))

    
    @abstractmethod
    def load(self) -> Iterable[Document]:
        """Load documents from a file."""
        documents = []
        for element in self._elements:
            yield Document(
                content=element.text,
                type=element.
                format=element.metadata.filetype,
                metadata=element.metadata,
                file_path=self.file_path,
                loader=self.__class__.__name__,
            )


    def aggregate_topics(self):
        
    
        topics = []
        topic_schema = {
            "title": "",
            "body": "",
            "metadata": {},
        }
        for doc in self.load():
            topic = Topic(title="", body="")
            
            if isinstance(doc.type, Title):
                topic.title = doc.content
                continue

            elif isinstance(doc.type, (Text, ListItem, FigureCaption, NarrativeText)):
                # bodies.append(doc.content)
                topic.body += doc.content
                topic.metadata = doc.metadata
            
            # topic has values other than topic_schema 's default values
            if topic.to_dc != topic_schema:
                topics.append(topic.to_dict())
            
        return topics
    
    @property
    def _elements(self) -> List[Element]:
        """Get the elements from the partition handler."""
        return self.partition_handler(filename=self.file_path, **self._kwargs)


class HtmlLoader(Loader):
    """Loader that uses unstructured to load HTML files."""
    @property
    def elements(self) -> List:
        return partition_html(filename=self.file_path, **self.unstructured_kwargs)
    
        




