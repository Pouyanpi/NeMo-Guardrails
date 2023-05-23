from typing import Callable, Dict

from unstructured.file_type import FileType
# from unstructured.file_type import EXT_TO_FILETYPE

from unstructured.partition.html import partition_html
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.doc import partition_doc
from unstructured.partition.xlsx import partition_xlsx


from unstructured.partition.common import exactly_one
from unstructured.partition.csv import partition_csv
from unstructured.partition.doc import partition_doc
from unstructured.partition.docx import partition_docx
from unstructured.partition.email import partition_email
from unstructured.partition.epub import partition_epub
from unstructured.partition.html import partition_html
from unstructured.partition.image import partition_image
from unstructured.partition.json import partition_json
from unstructured.partition.md import partition_md
from unstructured.partition.msg import partition_msg
from unstructured.partition.odt import partition_odt
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.ppt import partition_ppt
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.rtf import partition_rtf
from unstructured.partition.text import partition_text
from unstructured.partition.xlsx import partition_xlsx
from unstructured.partition.xml import partition_xml



EXT_TO_FILETYPE = {
    ".txt": FileType.TXT,
    ".text": FileType.TXT,
    ".eml": FileType.EML,
    ".xml": FileType.XML,
    ".htm": FileType.HTML,
    ".html": FileType.HTML,
    ".md": FileType.MD,
    ".docx": FileType.DOCX,
    # ".pdf": FileType.PDF,
    # ".jpg": FileType.JPG,
    # ".jpeg": FileType.JPG,
    # ".xlsx": FileType.XLSX,
    # ".pptx": FileType.PPTX,
    # ".png": FileType.PNG,
    # ".doc": FileType.DOC,
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

class PartitionFactory:
    """Factory for partitioning functions.
    
    Example:
        >>> partition_function = PartitionFactory.get_partition_function("html")
    
    """

    PARTITION_FUNCTIONS: Dict[FileType, Callable] = {
        FileType.HTML: partition_html,
        FileType.MD: partition_md,
        FileType.PDF: partition_pdf,
        FileType.DOCX: partition_docx,
        FileType.DOC: partition_doc,
        FileType.XLSX: partition_xlsx,

    }

    @staticmethod
    def get_partition_function(file_type: FileType) -> Callable:
        if file_type not in PartitionFactory.PARTITION_FUNCTIONS:
            raise ValueError(f"Unsupported file type: {file_type}")
        return PartitionFactory.PARTITION_FUNCTIONS[file_type]
    
    @staticmethod
    def get_partition_function_from_ext(ext: str) -> Callable:
        if ext not in EXT_TO_FILETYPE:
            raise ValueError(f"Unsupported file extension: {ext}")
        return PartitionFactory.get_partition_function(EXT_TO_FILETYPE[ext])


    
    