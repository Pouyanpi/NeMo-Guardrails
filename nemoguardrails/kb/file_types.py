from enum import Enum


EXT_TO_FILETYPE = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".jpg": FileType.JPG,
    ".jpeg": FileType.JPG,
    ".txt": FileType.TXT,
    ".text": FileType.TXT,
    ".eml": FileType.EML,
    ".xml": FileType.XML,
    ".htm": FileType.HTML,
    ".html": FileType.HTML,
    ".md": FileType.MD,
    ".xlsx": FileType.XLSX,
    ".pptx": FileType.PPTX,
    ".png": FileType.PNG,
    ".doc": FileType.DOC,
    ".zip": FileType.ZIP,
    ".xls": FileType.XLS,
    ".ppt": FileType.PPT,
    ".rtf": FileType.RTF,
    ".json": FileType.JSON,
    ".epub": FileType.EPUB,
    ".msg": FileType.MSG,
    ".odt": FileType.ODT,
    ".csv": FileType.CSV,
    None: FileType.UNK,
}

class FileType(Enum):
    """File types supported by NeMo."""
    # this was highly inspired by the file types in unstructured @github:unstructured

    UNK = 0

    # MS Office Types
    DOC = 10
    DOCX = 11
    XLS = 12
    XLSX = 13
    PPT = 14
    PPTX = 15
    MSG = 16

    # Adobe Types
    PDF = 20

    # Image Types
    JPG = 30
    PNG = 31

    # Plain Text Types
    EML = 40
    RTF = 41
    TXT = 42
    JSON = 43
    CSV = 44

    # Markup Types
    HTML = 50
    XML = 51
    MD = 52
    EPUB = 53

    # Compressed Types
    ZIP = 60

    # Open Office Types
    ODT = 70
