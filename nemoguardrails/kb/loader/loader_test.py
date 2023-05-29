from unittest.mock import patch
from nemoguardrails.kb.loader import DocumentLoader

@patch("nemoguardrails.kb.loader.PartitionFactory.get")
def test_get_partition_handler(mock_get):
    # Assuming PartitionFactory.get returns a mock object
    mock_get.return_value = "MockPartition"

    loader = DocumentLoader(file_path="path/to/file")
    handler = loader._get_partition_handler()

    # check if PartitionFactory.get was called with the correct arguments
    mock_get.assert_called_with("path/to/file")

    # check the return value
    assert handler == "MockPartition"


from unittest.mock import patch, PropertyMock
from nemoguardrails.kb.loader import DocumentLoader, Element, Document

@patch.object(DocumentLoader, "_elements", new_callable=PropertyMock)
def test_load(mock_elements):
    # Assume Element.text, Element.metadata.filetype and Element.metadata.to_dict return some mock values
    element = Element(text="mock text", metadata=Mock(filetype="mock filetype", to_dict=lambda: "mock metadata"))
    mock_elements.return_value = [element]

    loader = DocumentLoader(file_path="path/to/file")
    documents = list(loader.load())

    assert len(documents) == 1
    assert documents[0].content == "mock text"
    assert documents[0].type == type(element)
    assert documents[0].format == "mock filetype"
    assert documents[0].metadata == "mock metadata"
    assert documents[0].file_path == "path/to/file"
    assert documents[0].loader == "DocumentLoader"


from unittest.mock import patch, Mock
from nemoguardrails.kb.loader import DocumentLoader, Document, Title, Text, Topic

@patch.object(DocumentLoader, "load")
def test_combine_topics(mock_load):
    doc1 = Document(content="mock title", type=Title, metadata=Mock(to_dict=lambda: {}))
    doc2 = Document(content="mock body", type=Text, metadata=Mock(to_dict=lambda: {}))
    mock_load.return_value = [doc1, doc2]

    loader = DocumentLoader(file_path="path/to/file")
    topics = loader.combine_topics()

    assert len(topics) == 1
    assert topics[0]["title"] == "mock title"
    assert topics[0]["body"] == "mock body"
    assert topics[0]["metadata"] == {}
  


from unittest.mock import patch, Mock
from nemoguardrails.kb.loader import PdfLoader, Document, Text, Topic
from io import BytesIO
import PyPDF2
import requests

# Define a mock PDF page with extractText method
class MockPdfPage:
    def extractText(self):
        return "mock page text"


# Define a mock PDF reader with pages
class MockPdfReader:
    def __init__(self, num_pages):
        self.pages = [MockPdfPage() for _ in range(num_pages)]


@patch.object(PyPDF2, "PdfFileReader")
@patch.object(requests, "get")
def test_load_from_url(mock_get, mock_reader):
    mock_get.return_value = Mock(content=b"mock pdf content")
    mock_reader.return_value = MockPdfReader(num_pages=1)

    loader = PdfLoader(url="http://example.com/sample.pdf")
    documents = list(loader.load())

    assert len(documents) == 1
    assert documents[0].content == "mock page text"
    assert documents[0].type == Text
    assert documents[0].format == "pdf"
    assert documents[0].metadata == {"page_num": 0}
    assert documents[0].source == {"url": "http://example.com/sample.pdf"}
    assert documents[0].loader == "PdfLoader"


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_file(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    mock_file = Mock()
    mock_file.read.return_value = b"mock pdf content"

    loader = PdfLoader(file=mock_file)
    documents = list(loader.load())

    assert len(documents) == 1
    # other assertions omitted for brevity


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_filename(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    with patch("builtins.open", mock_open(read_data=b"mock pdf content")) as mock_file:
        loader = PdfLoader(filename="path/to/file.pdf")
        documents = list(loader.load())

    assert len(documents) == 1
    # other assertions omitted for brevity


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_text(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    loader = PdfLoader(text=b"mock pdf content")
    documents = list(loader.load())

    assert len(documents) == 1
    # other assertions omitted for brevity
