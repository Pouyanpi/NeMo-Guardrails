from typing import Callable, Dict, Union
import os
from pathlib import Path

from unstructured.file_type import FileType
# from unstructured.file_type import EXT_TO_FILETYPE

from unstructured.partition.common import exactly_one


from unstructured.partition.text import partition_text
from unstructured.partition.html import partition_html
from unstructured.partition.xml import partition_xml
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.doc import partition_doc


# NOTE: to use these partition functions, uncomment the import statements below
# TODO(Pouyanpi): Figure out which file types are planned to be supported

# from unstructured.partition.csv import partition_csv
# from unstructured.partition.xlsx import partition_xlsx
# from unstructured.partition.email import partition_email
# from unstructured.partition.epub import partition_epub
# from unstructured.partition.image import partition_image
# from unstructured.partition.json import partition_json
# from unstructured.partition.msg import partition_msg
# from unstructured.partition.odt import partition_odt
# from unstructured.partition.ppt import partition_ppt
# from unstructured.partition.pptx import partition_pptx
# from unstructured.partition.rtf import partition_rtf


# borrowed from unstructured.fileutils.filetype

EXT_TO_FILETYPE = {
    ".txt": FileType.TXT,
    ".text": FileType.TXT,
    ".xml": FileType.XML,
    ".htm": FileType.HTML,
    ".html": FileType.HTML,
    ".md": FileType.MD,
    ".docx": FileType.DOCX,
    ".doc": FileType.DOC,

    # ".eml": FileType.EML,
    # ".pdf": FileType.PDF,
    # ".jpg": FileType.JPG,
    # ".jpeg": FileType.JPG,
    # ".xlsx": FileType.XLSX,
    # ".pptx": FileType.PPTX,
    # ".png": FileType.PNG,
    # ".zip": FileType.ZIP,
    # ".xls": FileType.XLS,
    # ".ppt": FileType.PPT,
    # ".rtf": FileType.RTF,
    # ".json": FileType.JSON,
    # ".epub": FileType.EPUB,
    # ".msg": FileType.MSG,
    # ".odt": FileType.ODT,
    # ".csv": FileType.CSV,
    None: FileType.UNK,
}



class PartitionManager:
    """Factory for partition functions from unstructured.
    
    Example:
        >>> partition_function = PartitionFactory.get_partition_function(".html")
    
    """

    _PARTITION_FUNCTIONS: Dict[FileType, Callable] = {
        FileType.HTML: partition_html,
        FileType.MD: partition_md,
        FileType.PDF: partition_pdf,
        FileType.DOCX: partition_docx,
        FileType.DOC: partition_doc,
    }

    @staticmethod
    def get(file_identifier: Union[str, FileType, Path]) -> Callable:
        if isinstance(file_identifier, FileType):
            return PartitionFactory._get_by_filetype(file_identifier)
        elif os.path.isfile(file_identifier):
            file_type = PartitionFactory._detect_filetype(file_identifier)
            return PartitionFactory._get_by_filetype(file_type)
        elif isinstance(file_identifier, str) and file_identifier in EXT_TO_FILETYPE:
            return PartitionFactory._get_by_ext(file_identifier)
        else:
            raise ValueError(f"Invalid file identifier: {file_identifier}")

    @classmethod
    def register(cls, file_type: FileType, partition_function: Callable):
        cls._PARTITION_FUNCTIONS[file_type] = partition_function

    @classmethod
    def list(cls):
        return cls._PARTITION_FUNCTIONS.keys()

    @staticmethod
    def _get_by_filetype(file_type: FileType) -> Callable:
        try:
            return PartitionFactory._PARTITION_FUNCTIONS[file_type]
        except KeyError:
            raise FileTypeNotFoundError(f"Partition function not found for file type: {file_type}")

    @staticmethod
    def _get_by_ext(ext: str) -> Callable:
        try:
            file_type = EXT_TO_FILETYPE[ext]
            return PartitionFactory._get_by_filetype(file_type)
        except KeyError:
            raise FileExtensionNotFoundError(f"Partition function not found for file extension: {ext}")

    @staticmethod
    def _detect_filetype(file_identifier: Union[str, Path]) -> FileType:
        try:
            _, extension = os.path.splitext(str(file_identifier))
            return EXT_TO_FILETYPE[extension.lower()]
        except KeyError:
            raise FileTypeNotFoundError(f"File type not found for file identifier: {file_identifier}")