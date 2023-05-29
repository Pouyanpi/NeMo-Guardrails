from pathlib import Path
from unittest.mock import Mock

import pytest

from .partition_factory import PartitionFactory, 
from .partition_factory import FileTypeNotFoundError, FileExtensionNotFoundError
from .typing import FileType
from .partition_factory import partition_html
from .partition_factory import partition_md
from .partition_factory import partition_pdf
from .partition_factory import partition_docx
from .partition_factory import partition_doc

# Assuming 'mock_partition_function' is a mock function.
mock_partition_function = Mock()

def test_get_partition_function_by_filetype():
    partition_func = PartitionFactory.get(FileType.HTML)
    assert partition_func == partition_html

def test_get_partition_function_by_filepath():
    # Assuming that test.html is an existing file in the same directory.
    partition_func = PartitionFactory.get(Path(__file__).parent / "test.html")
    assert partition_func == partition_html

def test_get_partition_function_by_file_extension():
    partition_func = PartitionFactory.get(".html")
    assert partition_func == partition_html

def test_get_partition_function_invalid_identifier():
    with pytest.raises(ValueError):
        PartitionFactory.get(12345)  # Not a valid file identifier.

def test_register_partition_function():
    PartitionFactory.register(FileType.JSON, mock_partition_function)
    assert PartitionFactory._PARTITION_FUNCTIONS[FileType.JSON] == mock_partition_function

def test_unrecognized_file_type():
    with pytest.raises(FileTypeNotFoundError):
        PartitionFactory.get(FileType('unrecognized_file_type'))

def test_unrecognized_file_extension():
    with pytest.raises(FileExtensionNotFoundError):
        PartitionFactory.get('.unrecognized_extension')
