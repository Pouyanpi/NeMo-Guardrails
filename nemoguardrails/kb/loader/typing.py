from pydantic import BaseModel

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



from unstructured.file_utils.filetype import FileType




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

