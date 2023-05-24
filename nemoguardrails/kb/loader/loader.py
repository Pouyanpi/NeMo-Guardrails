from typing import Any, Callable, Iterable, List

from pydantic import BaseModel


from .typing import (
    Title,
    Text, 
    ListItem, 
    FigureCaption, 
    NarrativeText
)
from . import PartitionManager

# TODO: move Document and Topic to a separate file

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
    
    :param: file_path: The path to the file to load.
    :param: file: A file-like object using "r" mode --> open(filename, "r").
    :param: text: The string representation of the file to load.
    :param: url: The URL of a webpage to parse. Only for URLs that return an HTML document.
    :param: partition_handler: A partition handler to use for the loader.
    :param: kwargs: Additional keyword arguments to pass to the partition handler see `unstructured.partion`.

    
    Example:
        >>> from nemoguardrails.kb.loader import DocumentLoader
        >>> loader = DocumentLoader(file_path="path/to/file.md")
        >>> for document in loader.load():
        ...     print(document.content)
        ...     print(document.type)
        ...     print(document.format)
        ...     print(document.metadata)
        ...     print(document.file_path)
        ...     print(document.loader)

        >>> file_paths = ["file1.txt", "file2.txt", "file3.txt"]
        >>> loaders = [DocumentLoader(file_path=path) for path in file_paths]
        >>> for loader in loaders:
        ...     documents = loader.load()
        ...     # process the documents for each file here
    """
    def __init__(self, 
                 file_path: Optional[str] = None, 
                 file: Optional[IO] = None , 
                 text: Optional[str] = None, 
                 url: Optional[str] = None, 
                 partition_handler: Optional[Callable] = None ,
                 **kwargs: Any):
        """Initialize a DocumentLoader."""
        
        # _source is a dictionary that contains the source of the document
        # The source can be a file_path, file, text, or url

        self._source = {
            "filename": file_path,
            "file": file,
            "text": text,
            "url": url,
        }
        

        self._kwargs = kwargs
        self._partition_handler = partition_handler

    @property
    def partition_handler(self):
        if self._partition_handler is None:
            self._partition_handler = self._get_partition_handler()
        return self._partition_handler(**self._kwargs)

    def _get_partition_handler(self):
        """Get the partition handler for the loader."""
        #NOTE: PartitionManager currently only supports file_path
        #TODO: Add support for file, text, and url
        return PartitionManager.get(self.file_path)
    
    @property
    def _elements(self) -> List[Element]:
        """Get the elements from the partition handler."""
        return self.partition_handler(**self._source, **self._kwargs)
    
    @abstractmethod
    def load(self) -> Iterable[Document]:
        """Load documents from a file."""

        for element in self._elements:
            yield Document(
                content=element.text,
                type=element.
                format=element.metadata.filetype,
                metadata=element.metadata,
                file_path=self.file_path,
                loader=self.__class__.__name__,
            )


    def combine_topics(self):
        """Combine multiple documents into topics.

        This method aggregates the body of multiple documents into topics, using the title of each document 
        as the title of the corresponding topic. The resulting topics are represented 
        as dictionaries with keys for `title`, `body`, and `metadata`.
        
        It's important to note that each file can contain multiple elements, which can correspond to multiple documents. 
        One of these elements could be a Title. The text elements that follow the Title until the next Title is encountered 
        are considered to be the body of the current topic, with the Title serving as the title of the topic.
        
        Returns:
            A list of dictionaries, each representing a topic.
        """
        
        #TODO: is topics a good name for this?

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
    


class HtmlLoader(Loader):
    """Loader that uses unstructured to load HTML files."""
    @property
    def elements(self) -> List:
        return partition_html(**self._source, **self.unstructured_kwargs)
    
        




