from langchain.text_splitter import (
    CharacterTextSplitter,
    LatexTextSplitter,
    MarkdownTextSplitter,
    # NLTKTextSplitter,
    # SpacyTextSplitter,
    PythonCodeTextSplitter,
    TokenTextSplitter,
    # SentencePieceTextSplitter,
)

from abc import ABC, abstractmethod
from typing import Dict, Any, List


SPLITTERS = {
    "character": CharacterTextSplitter,
    "latex": LatexTextSplitter,
    "markdown": MarkdownTextSplitter,
    # "nltk": NLTKTextSplitter,
    # "spacy": SpacyTextSplitter,
    "python_code": PythonCodeTextSplitter,
    "token": TokenTextSplitter,
    # "sentencepiece": SentencePieceTextSplitter,
}


class SplitterRegistry:
    splitters = SPLITTERS
   
    def __init__(self, splitters: Dict[str, Any]) -> None:
        self.validate_splitters()

    def __get__(self, class_name: str):
        return self.get(class_name)

    @classmethod
    def get(cls, class_name):
        """
        Get a splitter by name.

        :param class_name: The name of the splitter.
        :raises KeyError: If the splitter name does not exist in the registry.
        """
        if class_name not in cls.splitters:
            raise KeyError(f"{class_name} does not exist in the registry")
        return cls.splitters.get(class_name)

    def validate_splitters(self) -> None:
        """
        Validate that all splitters have a 'split' method.

        :raises ValueError: If a splitter does not have a 'split' method.
        """
        for splitter_name, splitter in self.splitters.items():
            if not hasattr(splitter, "split_text") or not callable(splitter.split_text):
                raise ValueError(f"{splitter_name} does not have a 'split' method")


splitter_registry = SplitterRegistry(SPLITTERS)


# BEGIN: docstring_example
class Splitter(ABC):
    """
    Abstract class for text splitters.

    :param name: The name of the splitter.
    :type name: str, optional
    :param splitters: A dictionary of splitters.
    :type splitters: Dict[str, Any], optional

    :Examples:

    >>> splitter = Splitter(name="character")
    >>> splitter.split("Hello, world!")
    ['H', 'e', 'l', 'l', 'o', ',', ' ', 'w', 'o', 'r', 'l', 'd', '!']

    >>> splitter = Splitter(name="markdown")
    >>> splitter.split("# Hello, world!")
    ['<h1>Hello, world!</h1>']

    >>> splitter = Splitter(name="python_code")
    >>> splitter.split("def hello_world():\n    print('Hello, world!')\n")
    ['def hello_world():\n', '    print(', "'Hello, world!'", ')\n']

    """
    def __init__(self, name: str = None, splitters: Dict[str, Any] = None, **kwargs) -> None:
        self._name = name
        self._splitters = splitters or splitter_registry
        self._kwargs = kwargs

    def split(self, text: str) -> list[str]:
        """
        Split a text into chunks.

        :param text: The text to split.
        :type text: str
        :return: The list of chunks.
        :rtype: list[str]
        """
        splitter_name = self._name
        splitter = self.get_splitter(splitter_name)
        return splitter.split_text(text)

    def get_splitter(self, splitter_name: str = "character") -> "TextSplitter":
        """
        Get a splitter by name.

        :param splitter_name: The name of the splitter to get.
        :type splitter_name: str, optional
        :param **kwargs: Additional keyword arguments to pass to the splitter constructor.
        :raises ValueError: If the splitter name is invalid.
        :return: An instance of the selected splitter.
        :rtype: TextSplitter
        """
        splitter_class = self._splitters.get(splitter_name)
        if splitter_class is None:
            raise ValueError(f"Invalid splitter name: {splitter_name}")
        return splitter_class(**self._kwargs)


class TextSplitter(ABC):
    """Abstract class for text splitters."""
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """
        Split a text into chunks.

        :param text: The text to split.
        :type text: str
        :return: The list of chunks.
        :rtype: list[str]
        """
        raise NotImplementedError



from html.parser import HTMLParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

from html.parser import HTMLParser

class HtmlTextSplitter(RecursiveCharacterTextSplitter):
    """Attempts to split the text along HTML-formatted layout elements.
    
    :param separators: A list of separators to use.
    :type separators: List[str], optional

    :Examples:

    >>> splitter = HtmlTextSplitter()
    >>> splitter.split("<h1>Hello, world!</h1>")
    ['<h1>', 'Hello, world!', '</h1>']

    """

    def __init__(self, separators: List[str] = None, **kwargs: Any):
        """Initialize an HtmlTextSplitter."""
        super().__init__(**kwargs)

    def split_text(self, text: str) -> List[str]:
        """Split the text along HTML-formatted layout elements."""
        self._text = text
        self._separators = self._get_html_tags()
        print(self._separators)
        return super().split_text(text)

    def _get_html_tags(self) -> List[str]:
        """Extract HTML tags from a given text and return them as a list of separators."""
        class TagExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []

            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)

        parser = TagExtractor()
        parser.feed(self._text)
        tags = [f"</{tag}>" for tag in parser.tags]
        tags.extend([f"<{tag}>" for tag in parser.tags])
        print(tags)
        return tags


if __name__ == "__main__":
    splitter = HtmlTextSplitter(chunk_size=1, chunk_overlap=0)
    html_text = """
    <h1>Hello, world!</h1>
    <p>This is a paragraph.</p>
    <p>This is another paragraph.</p>
    <li>This is a list item.</li>
    <li>This is another list item.</li>
    """
    result = splitter.split_text(html_text)
    print(result)