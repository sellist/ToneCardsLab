from enum import Enum


class RendererType(str, Enum):
    STRING = "string"
    MARKDOWN = "markdown"
    ABC_JS = "abc_js"
    IMAGE = "image"
    LATEX = "latex"
    MERMAID = "mermaid"


class DeckExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

