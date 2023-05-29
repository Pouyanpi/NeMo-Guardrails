import pytest
from nemoguardrails.kb.loader import Document

def test_document_init():
    # Initialize a Document instance
    document = Document(content="test content",
                        type="text",
                        format="txt",
                        metadata={"author": "John Doe"},
                        file_path="/path/to/file",
                        loader="DocumentLoader")
    
    assert document.content == "test content"
    assert document.type == "text"
    assert document.format == "txt"
    assert document.metadata == {"author": "John Doe"}
    assert document.file_path == "/path/to/file"
    assert document.loader == "DocumentLoader"


from nemoguardrails.kb.loader import Topic

def test_topic_init():
    # Initialize a Topic instance
    topic = Topic(title="test title",
                  body="test body",
                  metadata={"author": "John Doe"})

    assert topic.title == "test title"
    assert topic.body == "test body"
    assert topic.metadata == {"author": "John Doe"}
